.. _ansicht:

===================
Öffentliche Ansicht
===================
Zur einfachen Einsicht für normale Nutzer ohne Zugangsrechte wurden eigene Templates und Skripte erstellt.

Page-wrapper
============
    ``wagtailtagging/templates/page_wrapper.html``
Alle Frontendseiten sind von diesem Wrapper abgeleitet. Er stellt eine allgemeine Stylingdatei und eine Menübar zur Verfügung. Die Menüpunkte beinhalten die Sektionen new, front, pages, images und documents. Bei new und front wird man zur Homepage mit der entsprechenden Flag weitergeleitet, bei pages, images und documents zu den browseable Rest-Endpoints. Die Modells für die angeführten  Seiten liegen in home/models.py

Homepage
========
    ``home/templates/home/home_page.html``

Dient als Landingpage, bei der noch kein Bild ausgewählt wurde. Das Template kann ohne Get-Attribute oder mit einer Front-Flag aufgerufen werden. Mit der Frontflag werden nur Bilder gezeigt die als solche im Backend markiert wurden (wie z.B. die Projektseite). Das Modell sieht wie folgt aus::

    class HomePage(Page):
        """Landing Page of wagtailTagging
        There are only displayed the menu and the first 100 thumbnails with headers.
        You can browse it normal mode or in front mode ?front=true
        """
        def get_last_children(self):
            """returns 100 children pages of Homepage"""
            try:
                return self.get_children().specific().reverse()[0:100]
            except IndexError:
                return []

        def get_last_front_children(self):
            """returns 100 children pages of Homepage with the front flag"""
            try:
                return ImageSelector.objects.filter(front=True).reverse()[0:100]
            except IndexError:
                return []


Image_Selector
=============
    ``home/templates/home/image_selector.html``
    
Wird ein Bild über eine Überschrift oder ein Thumbnail ausgewählt, so wird diese Anfrage mit dem Image_Selctor_Template gerendert. Neben dem Bild mit einer festgesetzten maximalen Höhe und breite, der Überschrift, dem Zeitstempel und dem Bildtext werden auch das Originalbild als auch der browseable Restendpoint verlinkt. Das entsprechende Modell::

    class ImageSelector(Page):
        """Model of a specific page
        In the ImageSelectorPage a resized image with all its information is displayed.
        Has like the Homepage two modes: all and front
        """
        main_image = models.ForeignKey(
            'home.CustomImage',
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name='+'
        )
        front = models.BooleanField(default=False, editable=True)
        date = models.DateField("Post date", default=date.today)
        intro = models.CharField(max_length=250, blank=True)
        body = RichTextField(blank=True)

        search_fields = Page.search_fields + (
            index.SearchField('intro'),
            index.SearchField('body'),
        )
        
        #content_panels for content creation in the CMS
        content_panels = Page.content_panels + [
            FieldPanel('front', widget=CheckboxInput),
            FieldPanel('date'),
            FieldPanel('intro'),
            ImageChooserPanel('main_image'),
            FieldPanel('body', classname="full")]
        
        #api_fields for the REST-interface
        api_fields = ('main_image', 'body', 'front', 'date', 'intro')
        
        #methods to display and navigate to neighbourimages
        def get_prev_front_sibling(self):
            """method for javascript navigation
            :return previous ImageSelector with a front flag"""
            for image_page in self.get_prev_siblings().specific():
                if image_page.front:
                    return image_page
            return None

        def get_next_cutted_siblings(self):
            """:return next 50 siblings to display thumbnails"""
            next_siblings = self.get_next_siblings().specific().reverse()
            len_next = len(next_siblings)
            start = len_next-50 if len_next-50 > 0 else 0
            return next_siblings[start:len_next]
        ...
        
Show_tags.js
============
    ``wagtailtagging/static/js/show_tags.js``
    
Für eine dynamische Ansicht ist das Skript show_tags.js verantwortlich. Neben der Anzeige der selektierten Bereiche und ausgeschnittenen Objekte über die zusammengehörigen Tags, wird zudem eine einfache Navigation über die Pfeiltasten zur Verfügung gestellt. Dreh und Angelpunkt der Anzeige ist das nachfolgende JSON-Objekt::

    var tags_to_selection = {};

Dies wird nachdem die Verhältnisgrößen kalkuliert wurden mit den passenden Daten aus dem Serverobjekt "selections" befüllt.  Das vorladen von benachbarten Bilder wurde nicht ausimplementiert, es steht aber mit 'json/method/object_id/' ein entsprechender Serverendpoint zur Verfügung. Die object_id entspricht der Bild-Id und method steht für eine der folgenden Funktionen::

    'get_prev_front_sibling','get_next_front_sibling',
    'get_next_cutted_siblings','get_prev_cutted_siblings',
    'get_next_cutted_front_siblings','get_prev_cutted_front_siblings'

