.. _erweiterungen:
========
Erweiterungen
========

Die zwei neuen Hauptfeatures - die multiple Objektauswahl und die Bildsegmentierung - wurden in die herkömmliche Wagtailoberfläche eingepflegt. Entweder wurden Benutzerinterfaces der herkömlichen `cropping Funktion <https://wagtail.io/features/image-cropping/>`_ übernommen oder eigene hinzugefügt. Dabei wurden die Javascriptbibliotheken `Jcrop <http://deepliquid.com/content/Jcrop.html>`_ für die Objektauswahl und `Konva <https://konvajs.github.io/>`_ zur Flächenmarkierung in der Bildsegmentierung genutzt.

======================
Multiple Objektauswahl

Für die Mehrfachauswahl von Objekten und der Zuweisung zu multiplen Tags wurde das edit.html Template überschrieben. Dies beinhaltet das Laden von externen Javascript und CSS Dateien wie wagtailtagging.css und wagtailtagging.js sowie eine erweiterte Speicherform und das Laden der alten Objekt-Tag-Zuweisungen mit zugehörigen Metadaten

wagtailtagging.js
=================
    ``wagtailtagging/static/js/wagtailtagging.js``
    
In wagtailtagging.js wurden Funktionen und Hilfsfunktionen gebündelt, die die Steuerung als auch die korrekte Umrechnung der Bildpunkte ermöglicht. Das Hauptdatenobjekt in der Speicherung und der Kommunikation mit dem Server stellt die json_message dar::

    var json_message = {"create":{}, "delete":[], "alter":[]};
    
Dieses JSON-Objekt wird beim Laden der Seite initiert und bei der Ausführung der Buttons "Save Conntections" und "Delete Scope" bearbeitet::

    function save_connections() {
        //saves the hightlighted tags and selections
        //as one connection to the json message
        updateJSON();
        release_section();
        current_tags = [];
        current_selections = {};
        $(".tag").css("background-color","#43b1b0");
        $(".selected").removeClass("selected");
        updateButtons();
    }
    
Bei save_connections erfolgt die Erneuerung von json_message in updateJSON, anschließend werden die Zwischenspeicher zurückgesetzt und die Styles und Buttons dem neuen Status angepasst. Dieselbe Funktion - nur ohne das Speichern - wird auch bei dem 'Cancel'-Button aufgerufen. Demgegenüber werden bei delete_scope nur die ausgewählte Selektion aus der json_message und dem Dombaum gelöscht.

models.py
=========
    ``home/models.py``
    
Die Datei models.py definiert neben den Modells für die Seiten (HomePage und ImageSelector) die abgeleiteten Modells für die Bilder und Bildausschnitte wie auch Funtionen zur Persistenz neuer Bilder und Ausschnitte. Zur Haltung eigener Bilder ist die Klasse CustomImage zuständig, die von dem abstrakten Modell AbstractImage abgeleitet wird::

    class CustomImage(AbstractImage):
        """Own imageclass
        Attributes:
            json        JSONField to get the informations from edit.html
            selections  JSONField to display the selections made in edit.html in the Rest-API
            has_page    BooleanField is False for new Images
            thumb_url   CharField could be used for javscript loading of an ImageSelectorPage
            resize_url   CharField could be used for javscript loading of an ImageSelectorPage
        """
        blanked_image = models.ForeignKey(BlankedImage, null=True, blank=True)
        json = JSONField(blank=True, null=True, default={})
        selections = JSONField(blank=True, null=True, default={})
        has_page = BooleanField(default=False)
        thumb_url = models.CharField(max_length=250, blank=True)
        resize_url = models.CharField(max_length=250, blank=True)
        blanked_url = models.CharField(max_length=250, blank=True)
        admin_form_fields = Image.admin_form_fields + (
            'json',
        )

        api_fields = ('selections', 'filename', 'thumb_url', 'resize_url', 'blanked_url', 'tags')

        def get_selections(self):
            return json.dumps(self.selections)

Für jedes hochgeladene Bild wird in create_page(sender, instance) eine ImageSelector(Page) erstellt und anschließend die has_page-Flag auf Wahr gesetzt. Das has_page-Attribut ist nötig um in dem Speicherhook die verschieden Modis unterscheiden zu könne::

    @receiver(post_save, sender=CustomImage)
    def post_save_image(sender, instance, **kwargs):
        """own hook, is called after an image is saved
        if the save call comes from edit.html create_cropped_image() is called.
        Else the call comes from the image uploader, so a new ImageSelectorPage is created.
        """
        if instance.json and 'endrecursion' in instance.json:
            # every create_cropped_image() call saves the image once again
            print 'end recursion'
        elif instance.json and not ('endrecursion' in instance.json):
            #create a new cropped image
            create_cropped_image(sender, instance)
        elif not instance.has_page:
            #a new ImageSelectorPage is created and saved
            create_page(sender, instance)


===================
Objektsegmentierung

In wagtailtagging/templates/drawing.html werden die Benutzereingaben zur Bildsegmentierung entgegengenommen, die auf dem Server mittels dem halbautomatischen OpenCV-Algorithmus `grabCut <http://docs.opencv.org/3.1.0/d8/d83/tutorial_py_grabcut.html>`_ segmentiert und in den Models gespeichert werden.

foreground_cropping.js
======================
    ``wagtailtagging/static/js/foreground_cropping.js``
Neben den Interaktionsfunktionalitäten läuft die Kommunikation und die Darstellung der Ergebnisse über diese JQuery-Datei. Zu den Interaktionen zählen:

#. Auswahl des Ausschnittes::
  
      $('#drop_down').on('change', function() {
        //get the (cropped) image id
        var id = $("option:selected", this)[0].id
        var new_selection = get_selection(id);
        //reset the canvas and init it with the new image id
        clear_canvas(new_selection);
      });

#. Auswahl und Benutzung des Vordergrundpinsels::

       $(document).on('click', '#foreground_button', function(){
        mode = 'brush';
        context.strokeStyle = "rgb(48,48,48)";
        });
        
   Das Zeichnen erfolgt bei dem Event::
   
        stage.on('contentMousemove.proto', function() {...});
        
   Hierbei werden die verschieden Zeichen Modis abgefragt und zwischen der gespeicherten und der kalkulierten Mausposition eine Linie gezeichnet.
   
#. Auswahl und Benutzung des Hintergrundpinsels::

    $(document).on('click', '#background_button', function(){
        mode = 'brush';
        context.strokeStyle = "rgb(100,200,215)";
    });

#. Auswahl und Benutzung des Radiergummis::

    $(document).on('click', '#eraser_button', function(){
        mode = 'eraser';
    });

#. Ein Bild-zoom über die rechte Maustaste, hierfür sind die Variablen stage.x, stage.y und stage.scale zuständig. Weitere Umgebungsvariablen werden beim Aufruf der Funktion zoom(stage, level) geändert.
#. Auswahl der Pinseldicke::

    $("#brush_size").change(function() {
        context.lineWidth = $( this ).val();
    });

#. Anstoßen der Kalkulation::
   
    $('#calculate_button').bind('click', data_object, calculate);

   Dabei wird das Canvas-Objekt in eine DataUrl umgewandelt und mit den nötigen Metadaten über create_post(message) an den Server geschickt. Bei einem erfolgreichen Datenaustausch wird das Ergebnis mittels drawImage(img) dargestellt.
#. Anstoßen des Speichervorgangs::

    $('#save_button').bind('click', data_object, save);
    
   Derselbe Vorgang wie bei der Kalkulation, nur die Speicherflag wird auf True gesetzt ``"save_clipping" : True``.

grabbing.py
===========
    ``wagtailtagging/grabbing.py``
    
Hier werden die nötigen Umwandlungen und Berechnungen für die Objektsegmentierung vorgenommen und letztendlich als Bilder und Masken abgespeichert. Über die Funktion ``create_clipping(request)`` die an die Url get_foreground angebunden ist, wird die Hauptfunktion::


    def get_mask_from_image(image, selection, cropped_image_link, save_result, image_object):
        """ generates the mask and blankes the image from the users input
        :param image: the mask from the clipping interface in wagtail as a png image
        :param selection: a dic with all selection parameters
        :param cropped_image_link: link to the already cropped image in the backend
        :param save_result: boolean value if True grabCut runs with a higher resolution
                            and the result is stored in the backend
        :param image_object: the image object from the model is either a CustomImage or a CroppedImage
        :return the generated mask from the grabCut-Algo
        ...
        """

aufgerufen und die Maske als Stream wieder zum Client geschickt. Innerhalb der Funktion werden die empfangenen base64 Daten dekodiert, das Bild für eine geringe Auflösung und somit kleineren Rechenaufwand herunterskaliert. Im Anschluss berechnet der grabCut-Algorithmus von OpenCV die Maske und speichert das Ergebnis bei gesetzter save_result Variable über ``update_blanked_image(file_path, image_object, object_id)`` in das Modell. Wem diese performancekritische Berechnung in OpenCV zu langsam ist, kann man bei entsprechender Hardware auf `NVIDIA Performance graphcut primitive <https://developer.nvidia.com/npp>`_ zurückgreifen. 

    
contour.py
==========
    ``wagtailtagging/contour.py``
    
Die Datei stellt eine Funktion zur Berechnungen einer Objektkontour bereit, die aber noch nicht im Frontend angezeigt wird und nicht im Backend persistiert wird. Diese und weitere Funktionen waren angedacht um Merkmale für Ähnlichkeitssuchen bereitstellen zu können.
