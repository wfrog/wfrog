import test
import yaml

class TestElement(test.Test1, yaml.YAMLObject):
    yaml_tag = "!test"
