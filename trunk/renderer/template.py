from Cheetah.Template import Template
from Cheetah.NameMapper import NotFound
import logging

class TemplateRenderer(object):
    """
    Executes a wrapped renderer and fills a template with the resulting data.
    """

    path = None
    renderer = None
    mime = "text/plain"

    logger = logging.getLogger("renderer.template")

    def __init__(self, path, renderer):
        self.path=path
        self.renderer=renderer

    def render(self,data={}, context={}):
        content = self.renderer.render(data, context)
        try:
            template = Template(file=file(self.path, "r"), searchList=[content])
            return [ self.mime, str(template) ]
        except NotFound:
            logger.error("Template '"+ self.path + "' not found.'")
            raise
