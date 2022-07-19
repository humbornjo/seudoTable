from enum import Enum

from django.db import models
from django.utils.timezone import now
from jsonfield import JSONField

# NOTE: I use spliteDB here, issue still exist
# After saving the model by modify the object, objective should be reimported
# incase the 'dictionary cant be resolved' problem (I dont know why)
# direct use in with the object defined in python wont harm

class GlobalStatusEnum(Enum):
    TODO = 'TODO'
    DOING = 'DOING'
    DONE = 'DONE'

class Table(models.Model):

    file_name = models.TextField()
    header = JSONField()
    ne_cols = JSONField(default=[])
    no_ann_cols = JSONField(default=[])

    global_status = models.CharField(max_length=15, choices=[(tag.name, tag.value) for tag in GlobalStatusEnum],
                                     default=GlobalStatusEnum.TODO.value)
    pub_date = models.DateTimeField(default=now)
    last_edit_date = models.DateTimeField(default=now)
    num_cols = models.PositiveIntegerField(default=1)
    num_rows = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.file_name


class TableData(models.Model):
    table = models.OneToOneField(Table, on_delete=models.CASCADE)
    header = JSONField()
    data_original = JSONField()
    data = JSONField()
    cands = JSONField(default={})

class TableSearch(models.Model):
    table = models.OneToOneField(Table, on_delete=models.CASCADE)

    step_num = models.PositiveIntegerField(default=1)

    direct_res = JSONField(default={})
    direct_dbp = JSONField(default={})

    seudo_res = JSONField(default={})
    seudo_dbp = JSONField(default={})

    history_wiki = JSONField(default = {"direct":{}, "seudo":{}})
    history_dbp = JSONField(default = {"wiki2db":{}, "label":{}, "abstract":{}, "type":{}})

    type_dict=JSONField(default={})