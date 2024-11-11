import constructs as constructs
import cdk8s as cdk8s
import cdk8s_plus_31 as kplus

class Deployment(cdk8s.Chart):
    def __init__(self, scope, id, *, bucket):
        super().__init__(scope, id)

