from django.shortcuts import render
from django.views.generic.base import View
from search.models import SoftwareType
from django.http import HttpResponse
import json
from elasticsearch import Elasticsearch
from datetime import datetime
import redis


client=Elasticsearch(hosts=["127.0.0.1"])

class IndexView(View):
    def get(self,request):
        topn_search=redis_cli.zrevrangebyscore("search_keywords_set","+inf","-inf",num=5,start=0)
        return render(request,"index.html",{"topn_search":topn_search})

class SearchSuggest(View):
    def get(self,request):
        key_words=request.GET.get('s','')
        re_datas=[]
        if key_words:
            s=SoftwareType.search()
            s=s.suggest('my_suggest',key_words,completion={
                "field":"suggest","fuzzy":{
                    "fuzziness":2
                },
                "size":10
            })

            suggestions=s.execute_suggest()
            for match in suggestions.my_suggest[0].options:
                source=match._source
                re_datas.append(source['title'])


        return HttpResponse(json.dumps(re_datas),content_type="application/json")



redis_cli=redis.StrictRedis()


class SearchView(View):
    def get(self,request):
        #获取关键字
        key_words=request.GET.get("q","")

        redis_cli.zincrby("search_keywords_set",key_words)
        topn_search=redis_cli.zrevrangebyscore("search_keywords_set","+inf","-inf",start=0,num=5)

        #获取当前页码
        page=request.GET.get("p",'')
        try:
            page=int(page)
        except:
            page=0
        software_count=redis_cli.get("software_count")
        start_time=datetime.now()
        response=client.search(
            index="software",
            body={
                "query":{
                    "multi_match":{
                        "query":key_words,
                        "fields":["title","content"]
                    }
                },
                "from":page*10,
                "size":10,
                "highlight":{
                    "pre_tags":['<span class="keyWord">'],
                    "post_tags":['</span>'],
                    "fields":{
                        "title": {},
                        "content": {}
                    }
                }
            }
        )

        end_time=datetime.now()
        last_time=(end_time-start_time).total_seconds()

        total_nums=response["hits"]["total"]
        if(total_nums%10)>0:
            page_nums=int(total_nums/10)+1
        else:
            page_nums=int(total_nums/10)
        hit_list=[]
        for hit in response["hits"]["hits"]:
            hit_dict={}
            if "title" in hit["highlight"]:
                hit_dict["title"]="".join(hit["highlight"]["title"])
            else:
                hit_dict["title"]=hit["_source"]["title"]
            if "content" in hit["highlight"]:
                #因为在highlight中存储的是数组，我们要通过join变为str
                hit_dict["content"]="".join(hit["highlight"]["content"])[:500]
            else:
                hit_dict["content"]=hit["_source"]["content"][:500]

            hit_dict["updatetime"]=hit["_source"]["updatetime"]
            hit_dict["url"]=hit["_source"]["url"]
            hit_dict["size"]=hit["_source"]["size"]
            hit_dict["good_rate"]=hit["_source"]["good_rate"]
            hit_dict["thumbup_nums"]=hit["_source"]["thumbup_nums"]

            hit_list.append(hit_dict)


        return render(request,"result.html",{"topn_search":topn_search,"software_count":software_count,"last_time":last_time,"page_nums":page_nums,"total_nums":total_nums,"page":page,"all_hits":hit_list,"key_words":key_words})


