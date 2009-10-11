import renderer

class DataRenderer(object):
    """
    Executes a data query and pass the result to a wrapped renderer.

    [ Properties ]

    source:
        A data source performing the query and returning a data structure.

    renderer:
        A renderer called after the query was performed.
        The data structure is passed as parameter.
    """

    source=None
    renderer=None

    def render(self,data={}, context={}):
        assert self.source is not None, "'data.source' must be set"
        assert self.renderer is not None, "'data.renderer' must be set"
        assert renderer.is_renderer(self.renderer), "'data.renderer' must be a renderer"
        new_data = self.source.execute(data, context)
        new_data.update(data)
        return self.renderer.render(new_data, context)
