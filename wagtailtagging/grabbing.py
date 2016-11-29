import numpy as np
import cv2
from io import BytesIO
import base64
import contour

from home.models import update_blanked_image


# to get cv2 in virtualenv:
# cp cp /usr/lib/python2.7/dist-packages/cv*
# ~/virtualenvs/wagtailtagging.nmy.de-v1/lib/python2.7/site-packages/


def get_mask_from_image(image, selection, cropped_image_link, save_result, image_object):
    """ generates the mask and blankes the image from the users input

    :param image: the mask from the clipping interface in wagtail as a png image
    :param selection: a dic with all selection parameters
    :param cropped_image_link: link to the already cropped image in the backend
    :param save_result: boolean value if True grabCut runs with a higher resolution
                        and the result is stored in the backend
    :param image_object: the image object from the model is either a CutomImage or a CroppedImage
    :return the generate mask from the grabCut-Algo
    """
    print 'get mask...\n image reading...'

    # calculate the selection rect to run grabCur only with this as given input
    x = selection["x"]
    y = selection["y"]
    width = selection["width"]
    height = selection["height"]
    rect = (x, y, width, height)

    # get the cropped image from the backend
    # if you want to use the rect mode you have to use the full image instead
    cropped_original = cv2.imread(cropped_image_link)

    # convert the user mask to a numpy array
    img_stream = BytesIO(decode_base64(image.split(",")[1]))
    img_array = np.asarray(bytearray(img_stream.read()), dtype=np.uint8)
    mask = cv2.imdecode(img_array, cv2.CV_LOAD_IMAGE_COLOR)

    # save the mask shape before it is reduced
    frontend_size = mask.shape

    # reduce the image and mask to a small and similar size
    mask, cropped = resize_mask_and_image(mask, cropped_original, 400, selection)
    print "mask and image resized"

    # convert the mask values to the disired values from grabCut
    newmask = []
    for line in mask:
        row = []
        for pixel in line:
            if pixel[0] == 100:
                row.append(0)
            elif pixel[0] == 48:
                row.append(1)
            else:
                row.append(2)
        newmask.append(row)

    newmask = np.array(newmask, np.uint8)
    print newmask.shape
    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)

    if save_result:
        # run grabCut with highest resolution
        cropped_size = cropped_original.shape
        newmask = cv2.resize(newmask, (cropped_size[1], cropped_size[0]), interpolation=cv2.INTER_NEAREST)
        cv2.grabCut(cropped_original, newmask, rect, bgdModel, fgdModel, 2, cv2.GC_INIT_WITH_MASK)
        save_mask = cv2.resize(newmask, (cropped_size[1], cropped_size[0]), interpolation=cv2.INTER_NEAREST)
        save_mask_contour(selection['id'],save_mask, cropped_original, image_object)
    else:
        # run grabCut with a low solution
        cv2.grabCut(cropped, newmask, rect, bgdModel, fgdModel, 2, cv2.GC_INIT_WITH_MASK)

    newmask = cv2.resize(newmask, (frontend_size[1], frontend_size[0]), interpolation=cv2.INTER_NEAREST)

    return newmask


def decode_base64(data):
    """Decode base64, padding being optional.

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    missing_padding = 4 - len(data) % 4
    if missing_padding:
        data += b'='*missing_padding
    return base64.decodestring(data)


def resize_mask_and_image(mask, image, smallest_edge, selection):
    """resizes the given image and corresponding mask
    if the image is not to small, one edge is one reduced to the value of smallest_edge

    :param mask: the already converted user input
    :param image: the cropped image from the backend
    :param smallest_edge: the value of the smallest edge
    :param selection: a dic with all selection parameters
    :returns: the resized image and mask

    """
    # check if the size is allready to small
    if (mask.shape[0] < smallest_edge) or (mask.shape[1] < smallest_edge):
        # check if the mask and image have the same size
        if mask.shape[1] != selection["width"] or mask.shape[0] != selection["height"] or image.shape[1] != selection["width"] or image.shape[0] != selection["height"]:
            print('resize image and mask')
            mask = cv2.resize(mask, (selection["width"], selection["height"]), interpolation=cv2.INTER_NEAREST)
            image = cv2.resize(image, (selection["width"], selection["height"]), interpolation=cv2.INTER_NEAREST)
        print(mask.shape[1], selection["width"])
        assert(mask.shape[1] == selection["width"])
        assert(mask.shape[0] == selection["height"])
        assert(image.shape[1] == selection["width"])
        assert(image.shape[0] == selection["height"])

        return mask, image

    # calculate the biggest posibible size given by the smallest edge
    biggest_shape = get_smallest_shape(mask.shape, smallest_edge)

    # fails some times
    # assert(resize_shape(mask.shape, smallest_edge) == resize_shape(image.shape, smallest_edge))

    print("resize mask with biggest shape:")
    print(biggest_shape)
    mask = cv2.resize(mask, (biggest_shape[1], biggest_shape[0]), interpolation=cv2.INTER_NEAREST)
    image = cv2.resize(image, (biggest_shape[1], biggest_shape[0]), interpolation=cv2.INTER_NEAREST)

    return mask, image


def compare_shapes(shape_one, shape_two):
    """compares the sizes of the given shapes

    :param shape_one: the first shape
    :param shape_two: the second shape
    :returns: True if shape_one is smaller else False

    """
    if shape_one[0] < shape_two[1] and shape_one[1] < shape_two[1]:
        return True
    else:
        return False


def get_smallest_shape(shape, smallest_edge):
    """
    :param shape: the shape of the selection or mask
    :param smallest_edge: size of the smallest edge
    :returns: smallest shape with one edge with the size of smalles_edge

    """
    # resize shape[0] to smallest_edge
    factor = 1.0*smallest_edge/shape[0]
    print factor
    first_shape = (smallest_edge, int(round(shape[1]*factor)))
    print first_shape

    # resize shape[1] to smallest_edge
    factor = 1.0*smallest_edge/shape[1]
    second_shape = (int(round(shape[0]*factor)), smallest_edge)

    # return the biggest shape
    if compare_shapes(first_shape, second_shape):
        return second_shape
    else:
        return first_shape


def save_mask_contour(object_id, new_mask, cropped_original, image_object):
    """saves the mask as a transparent blanked image to the backend
    the contour could be calculated but is not stored
    for storing the contour to the backend one more calculation to the chaincode is necessary

    :param object_id: the id of the selection, -1 for the whole image
    :param new_mask: the resized output from grabCut
    :param cropped_original: the cropped image from the backend
    :param image_object: the object model from the backend

    """
    mask2 = np.where((new_mask == 2) | (new_mask == 0), 0, 1).astype('uint8')

    path = "media/blanked_images/"
    if object_id == -1:
        file_path = path+"blanked_original_image_"+str(image_object.id)+".png"
    else:
        file_path = path+"blanked_cropped_image_"+str(image_object.id)+".png"

    create_image(file_path, cropped_original, mask2, transparency=True)

    # update the model
    update_blanked_image(file_path, image_object, object_id)

    # create for demonstrational stuff the contour
    # contour_mask = contour.calculate_contour(new_mask)
    #
    # img = cropped_original*contour_mask[:,:,np.newaxis]
    # cv2.imwrite( "contour_mask_Image.jpg", img )


def create_image(file_path, cropped_image, mask, transparency=True):
    """calculates the image and saves it to the given path

    :param file_path: the path where the picture is stored
    :param mask: the resized output from grabCut
    :param cropped_image: the cropped image from the backend
    :param transparency: if True all pixel out of the mask are setted as transparence
                         if False all pixel out of the mask are setted as black pixels

    """
    if transparency:
        image_array = []
        for row in range(len(mask)):
            image_row = []
            for pixel in range(len(mask[row])):
                np_pixel = cropped_image[row][pixel]
                image_pixel = [np_pixel[0], np_pixel[1], np_pixel[2]]
                if mask[row][pixel] == 0:
                    image_pixel.append(0)
                else:
                    image_pixel.append(255)
                image_row.append(image_pixel)
            image_array.append(image_row)
        np_image = np.array(image_array)

        cv2.imwrite(file_path, np_image)
    else:
        img = cropped_image*mask[:, :, np.newaxis]
        cv2.imwrite(file_path, img)
