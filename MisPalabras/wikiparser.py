from xml.sax.handler import ContentHandler
from xml.sax import make_parser


class WikiHandler(ContentHandler):
    def __init__(self):
        super().__init__()
        self.inContent = False
        self.content = ""
        self.body = ""
        self.definition = ""

    def startElement(self, name, attrs):
        if name == 'extract':
            self.inContent = True

    def endElement(self, name):
        if name == 'extract':
            self.body = self.content
            self.content = ""
            self.inContent = False
            self.definition = self.body

    def characters(self, chars):
        if self.inContent:
            self.content = self.content + chars


class WikiChannel:
    def __init__(self, stream):
        self.parser = make_parser()
        self.handler = WikiHandler()
        self.parser.setContentHandler(self.handler)
        self.parser.parse(stream)

    def definition(self):
        return self.handler.definition
