class SimulatorQuery(object):
    """
    Return a simulated harcoded data.
    """

    query=None
    renderer=None

    def __init__(self, query, renderer):
        self.query=query
        self.renderer=renderer

    def execute(self,data={}, context={}):
        return {
            "temp" : {
                "value" : 3,
                "min" : 1,
                "max" : 6,
                "unit" : "C",
                "series" : {
                    "lbl" : [ "12:00", "13:00", "14:00", "15:00" ],
                    "avg" : [ 3, 5, 6, 6 ],
                    "min" : [ 1, 4, 3, 3 ],
                    "max" : [ 5, 6, 8, 12 ]
                    }
                }
            }        
