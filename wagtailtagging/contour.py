import numpy as np
import copy


def calculate_contour(mask):
    print('calculate contour')
    bigger_mask = copy.deepcopy(mask)
    print(bigger_mask.shape)
    width = bigger_mask.shape[1]
    height = bigger_mask.shape[0]

    print('height: '+str(height))
    print('width: '+str(width))
    print(bigger_mask[height-1][width-1])

    contour_mask = np.zeros(shape=mask.shape)

    for line in range(height):
        for pixel in range(width):
            if mask[line][pixel] == 1 or mask[line][pixel] == 3:
                if line == 0 or pixel == 0 or line == height-1 or pixel == width-1:
                    contour_mask[line][pixel] = 1
                else:
                    bigger_mask[line-1][pixel-1] = 1
                    bigger_mask[line-1][pixel] = 1
                    bigger_mask[line][pixel-1] = 1

                    bigger_mask[(line+1)%height][(pixel+1)%width] = 1
                    bigger_mask[(line+1)%height][pixel] = 1
                    bigger_mask[line][(pixel+1)%width] = 1

                    bigger_mask[line-1][(pixel+1)%width] = 1
                    bigger_mask[(line+1)%height][pixel-1] = 1

    for line in range(height):
        for pixel in range(width):
            if contour_mask[line][pixel] != 1:
                if mask[line][pixel] != bigger_mask[line][pixel]:
                    contour_mask[line][pixel] = 1
                if mask[line][pixel] == 3 and bigger_mask[line][pixel] == 1:
                    contour_mask[line][pixel] = 0

    return contour_mask
