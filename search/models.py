from django.db import models

# Create your models here.
from datetime import datetime
from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Keyword, Text

#链接到本地的es  hosts为数组，可以传入多个es地址
from elasticsearch_dsl.connections import connections
connections.create_connection(hosts=["localhost"])

#自动补全功能
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer
class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}
ik_analyzer=CustomAnalyzer("ik_max_word",filter=["lowercase"])

#es创建索引 类似于mysql的create table
class SoftwareType(DocType):
    #自动补全功能
    suggest=Completion(analyzer=ik_analyzer)

    title =Text(analyzer="ik_max_word")
    url = Keyword()
    url_object =Keyword()
    size = Keyword()
    updatetime = Date()
    good_rate=Keyword()
    thumbup_nums=Keyword()
    content=Text(analyzer="ik_max_word")

    #下面是创建数据库的名称和表
    class Meta:
        index="software"
        doc_type="xixi"



if __name__=="__main__":
    SoftwareType.init()