class MultiRenderer(object):
    """
    Wraps a list of renderers and delegates the rendering to them.
    The result is a dictionary containing the result of each rende-
    rer indexed by names.

    Properties

    renderers:
        A dictionary in which keys are names and values are the renderer
        objects the rendering is delegated to.

        If the key name contains an underscore, that means that the data
        passed to
    """

    renderers={}

    def render(self,data,context={}):
        result = {}
        for name, r in self.renderers.iteritems():
            parts = name.split("_")
            if len(parts) > 1 and data.has_key(parts[0]):
                data_to_render = data[parts[0]]
            else:
                data_to_render = data

            result[name] = r.render(data_to_render, context)
        return result
