from docx import Document

class TzParser(object):
    def __init__(self, filenames, volume):
        self.files = filenames
        self.volume = volume
