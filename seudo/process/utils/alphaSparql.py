from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.parse import unquote
import socks
import socket
socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 7890)
socket.socket = socks.socksocket

import ssl
ssl._create_default_https_context = ssl._create_unverified_context


# b = TextBlob("maner")
#
# print(b.correct())

class MySPARQL:
    def __init__(self,endpoint):
        self.endpoint=endpoint
        self.sparql = SPARQLWrapper(self.endpoint)
        self.sparql.setReturnFormat(JSON)
        self.sparql.setTimeout(15)

    def set_query(self,query):
        self.sparql.setQuery(query)

    def fuzzy_search(self,mention):
        if not mention:
            return None
        result_list = []  # 可能有多个返回结果
        queryTypes = """
        SELECT DISTINCT str(?url) as ?url  str(?label) as ?label 
        WHERE {?url rdfs:label ?label 
        FILTER (lang(?label) = "en")
        FILTER CONTAINS (?label,'""" + mention + """"')
        }    
        """
        self.set_query(queryTypes)
        results = self.sparql.query().convert()
        # print(mention, result_list)

        for result in results["results"]["bindings"]:
            result_list.append(result["mtype"]["value"])

        if len(result_list) == 0:
            return None

        return result_list

    def direct_search(self,mention):
        if not mention:
            return None

        queryTypes = """
            SELECT DISTINCT str(?label) as ?label
            WHERE{{
                {{
                    <%s> rdfs:label ?label
                }}
            FILTER (lang(?label)="en").
            }}
            """ % mention

        self.set_query(queryTypes)
        results = self.sparql.query().convert()
        if len(results["results"]["bindings"]) == 0:
            return None
        else:
            return mention

    def redirect_search(self,mention):
        if not mention:
            return None

        queryTypes = """
            SELECT DISTINCT str(?redirect) as ?redirect
            WHERE {{
                <%s> dbo:wikiPageRedirects ?redirect.
            }}
            """ % mention

        self.set_query(queryTypes)
        results = self.sparql.query().convert()
        if len(results["results"]["bindings"]) == 0:
            return None
        else:
            return results["results"]["bindings"][0]["redirect"]["value"]

    def get_label(self,mention):
        if not mention:
            return None

        queryTypes = """
            SELECT DISTINCT str(?label) as ?label
            WHERE {{
                {{
                    <%s> rdfs:label ?label
                }}
                FILTER (lang(?label)="en").
            }}
            """ % mention

        self.set_query(queryTypes)
        results = self.sparql.query().convert()
        if len(results["results"]["bindings"]) == 0:
            return None
        else:
            return results["results"]["bindings"][0]["label"]["value"]

    def get_type(self,mention):
        if not mention:
            return []
        result_list = []  # 可能有多个返回结果
        queryTypes = """
                SELECT DISTINCT str(?mtype) as ?mtype 
                WHERE {{
                    {{
                        <%s> rdf:type ?mtype.
                    }}
                FILTER (strstarts(str(?mtype),'http://dbpedia.org/ontology/'))
                }}
            """ % mention

        self.set_query(queryTypes)
        results = self.sparql.query().convert()

        for result in results["results"]["bindings"]:
            result_list.append(result["mtype"]["value"])

        if len(result_list) == 0:
            return []

        return result_list

    def get_check(self,obj,pred,sub):
        queryTypes = """
            SELECT DISTINCT COUNT(*) as ?num
            WHERE {{
                {{
                    <%s> <%s> <%s>.
                }}
            }}
        """ % (obj,pred,sub)

        self.set_query(queryTypes)
        results = self.sparql.query().convert()

        res=bool(int(results["results"]["bindings"][0]["num"]["value"]))

        return res

    def get_candidate(self, text_for_query):
        if text_for_query == "":
            return []
        sql=u'''
            SELECT DISTINCT str(?s) as ?s str(?abstract) as ?abstract 
            WHERE {{
                {{
                ?s dbo:abstract ?abstract.
                ?s a ?type.
                ?s rdfs:label ?label.
                ?label <bif:contains> "%s".
                }}
            FILTER NOT EXISTS { ?s dbo:wikiPageRedirects ?r2}.
            FILTER (lang(?label) = "en").
            FILTER (!strstarts(str(?s), 'http://dbpedia.org/resource/Category:')). 
            FILTER (!strstarts(str(?s), 'http://dbpedia.org/property/')).
            FILTER (!strstarts(str(?s), 'http://dbpedia.org/ontology/')). 
            FILTER (strstarts(str(?type), 'http://dbpedia.org/ontology/')). 
            }}
            ORDER BY ASC(strlen(?label))
            LIMIT 10
            ''' % text_for_query
        self.set_query(sql)

        results = self.sparql.query().convert()["results"]["bindings"]

        return results

    def get_abstract(self,mention):
        if not mention:
            return None

        queryTypes = """
            SELECT str(?a) as ?a 
            WHERE {{
                {{
                    <%s> <http://dbpedia.org/ontology/abstract> ?a.
                }}
                FILTER (lang(?a) = "en").
            }}  
            """ % mention

        self.set_query(queryTypes)
        results = self.sparql.query().convert()
        if len(results["results"]["bindings"]) == 0:
            return None
        return results["results"]["bindings"][0]["a"]["value"]

    def get_relation(self,obj,subj):
        queryTypes = ("""
            SELECT DISTINCT str(?a) as ?a 
            WHERE {{
                {{
                    <%s> ?a <%s>.
                }}
            FILTER (strstarts(str(?a), 'http://dbpedia.org/ontology/')).
            FILTER (!strstarts(str(?a), 'http://dbpedia.org/ontology/wikiPageWikiLink')).
            }}
            """ % (obj,subj))
        # print(queryTypes)

        self.set_query(queryTypes)
        results = self.sparql.query().convert()
        # print(results)
        if len(results["results"]["bindings"]) == 0:
            return None
        return results["results"]["bindings"][0]["a"]["value"]

    def get_relsubj(self,obj,rel):
        queryTypes = ("""
            SELECT DISTINCT str(?a) as ?a 
            WHERE {{
                {{
                    <%s> <%s> ?a.
                }}
            FILTER (strstarts(str(?a), 'http://dbpedia.org/resource/')).
            }}
            """ % (obj,rel))
        # print(queryTypes)

        self.set_query(queryTypes)
        results = self.sparql.query().convert()
        # print(results)
        if len(results["results"]["bindings"]) == 0:
            return None
        return results["results"]["bindings"][0]["a"]["value"]

    def get_relobj(self,rel,subj):
        queryTypes = ("""
            SELECT DISTINCT str(?a) as ?a 
            WHERE {{
                {{
                    ?a <%s> <%s>.
                }}
            FILTER (strstarts(str(?a), 'http://dbpedia.org/resource/')).
            }}
            """ % (rel,subj))
        # print(queryTypes)

        self.set_query(queryTypes)
        results = self.sparql.query().convert()
        # print(results)
        if len(results["results"]["bindings"]) == 0:
            return None
        return results["results"]["bindings"][0]["a"]["value"]

    def get_disambiguation(self, query_text):
        if not query_text:
            return []

        query_text = 'http://dbpedia.org/resource/' + query_text + '_(disambiguation)'

        query = """
            SELECT DISTINCT str(?disa) as ?disa
              WHERE 
              {{
                {{
                  SELECT DISTINCT str(?disa) as ?disa ?abstract 
                  WHERE 
                  {{
                    <%s> dbo:wikiPageWikiLink ?disa.
                    FILTER (!strstarts(str(?disa), 'http://dbpedia.org/resource/Category:')).
                    FILTER (strstarts(str(?disa), 'http://dbpedia.org/resource/')).
                  }}
                }}
                UNION
                {{
                  SELECT DISTINCT str(?disa) as ?disa ?abstract 
                  WHERE 
                  {{
                    <%s> dbo:wikiPageRedirects ?redirect.
                    ?redirect dbo:wikiPageWikiLink ?disa.
                    FILTER (!strstarts(str(?disa), 'http://dbpedia.org/resource/Category:')).
                    FILTER (strstarts(str(?disa), 'http://dbpedia.org/resource/')).            
                  }}
                }}
              }}
            """ % (query_text, query_text)

        self.set_query(query)
        results = self.sparql.query().convert()
        if len(results["results"]["bindings"]) == 0:
            return []
        else:
            res_list = []
            for res_dict in results["results"]["bindings"]:
                res_list.append(res_dict["disa"]["value"])
            return res_list

    def get_property(self,mention):
        if not mention:
            return []

        queryTypes = """
            SELECT DISTINCT str(?prop) as ?prop str(?val) as ?val 
            WHERE {{
                {{
                    <%s> ?prop ?val.
                }}
            FILTER (strstarts(str(?prop),'http://dbpedia.org/ontology/')).
            FILTER (!strstarts(str(?prop),'http://dbpedia.org/ontology/wikiPageWikiLink')).  
            FILTER (strstarts(str(?val),'http://dbpedia.org/resource/')).  
            }}
            """ % mention

        self.set_query(queryTypes)
        results = self.sparql.query().convert()
        if len(results["results"]["bindings"]) == 0:
            return []
        else:
            res_list=[]
            for res_dict in results["results"]["bindings"]:
                res_list.append([res_dict["prop"]["value"], res_dict["val"]["value"]])
            return res_list

    def get_wiki2db(self,wikimen):
        if not wikimen:
            return None


        queryTypes = """
            SELECT DISTINCT str(?val) as ?val 
            WHERE {{
                {{
                    ?val foaf:isPrimaryTopicOf <%s>.
                }}
            }}
            """ % wikimen

        self.set_query(queryTypes)
        results = self.sparql.query().convert()
        if len(results["results"]["bindings"]) == 0:
            return None
        else:
            return results["results"]["bindings"][0]["val"]["value"]

    def get_subcls(self, ont):
        if not ont:
            return None

        queryTypes = """
                SELECT DISTINCT str(?val) as ?val 
                WHERE {{
                    {{
                        <%s> rdfs:subClassOf ?val.
                        FILTER (strstarts(str(?val),'http://dbpedia.org/ontology/') || strstarts(str(?val),'http://www.w3.org/2002/07/owl#Thing')).
                    }}
                }}
            """ % ont

        self.set_query(queryTypes)
        results = self.sparql.query().convert()
        if len(results["results"]["bindings"]) == 0:
            return None
        else:
            return results["results"]["bindings"][0]["val"]["value"]

    def get_equcls(self, ont):
        if not ont:
            return None

        result_list=[]

        queryTypes = """
            SELECT DISTINCT str(?val) as ?val 
            WHERE {{
                {{
                    ?val owl:equivalentClass <%s>.
                }}
            }}
            """ % ont

        self.set_query(queryTypes)
        results = self.sparql.query().convert()

        for result in results["results"]["bindings"]:
            result_list.append(result["val"]["value"])

        return result_list

    def get_seudodisam(self, query_text, query_type):
        if not query_text:
          return []

        query_text='http://dbpedia.org/resource/'+query_text.replace(' ','_').replace('"','').replace("'",'')+'_(disambiguation)'

        query = f"""SELECT DISTINCT str(?disa) as ?disa
                WHERE 
                {{
                    {{
                      SELECT DISTINCT str(?disa) as ?disa
                      WHERE 
                      {{
                        <{query_text}> dbo:wikiPageWikiLink ?disa.
                        ?disa rdf:type <{query_type}>.                    
                        FILTER (!strstarts(str(?disa), 'http://dbpedia.org/resource/Category:')).
                        FILTER (strstarts(str(?disa), 'http://dbpedia.org/resource/')).
                      }}
                    }}
                    UNION
                    {{
                      SELECT DISTINCT str(?disa) as ?disa
                      WHERE 
                      {{
                        <{query_text}> dbo:wikiPageRedirects ?redirect.
                        ?redirect dbo:wikiPageWikiLink ?disa.
                        ?disa rdf:type <{query_type}>.
                        FILTER (!strstarts(str(?disa), 'http://dbpedia.org/resource/Category:')).
                        FILTER (strstarts(str(?disa), 'http://dbpedia.org/resource/')).            
                      }}
                    }}
                }} ORDER BY strlen(str(?disa)) LIMIT 5"""
        self.set_query(query)
        results = self.sparql.query().convert()
        if len(results["results"]["bindings"]) == 0:
          return []
        else:
          res_list=[]
          for res_dict in results["results"]["bindings"]:
              res_list.append(res_dict["disa"]["value"])
          return res_list[:3]

    def get_seudocand(self, query_text, query_type):
        if not query_text:
          return []
        lang='"en"'
        token_for_query = query_text.split(' ')
        token_for_query = list(set(list(filter(lambda item: len(item) > 3, token_for_query))))
        query_text = '"'+token_for_query[0]+'"'
        for token in token_for_query[1:]:
          query_text+=' AND '+'"'+token+'"'

        query = f"""SELECT DISTINCT str(?url) as ?url
            WHERE 
            {{
                {{
                  SELECT DISTINCT str(?url) as ?url
                  WHERE 
                  {{
                    ?url rdfs:label ?label.
                    ?url rdf:type <{query_type}>.
                    ?label <bif:contains> '({query_text})'.
                    FILTER (lang(?label) = {lang}).
                  }}    
                }}
                UNION
                {{
                  SELECT DISTINCT str(?url) as ?url
                  WHERE 
                  {{
                    ?s dbo:wikiPageRedirects ?url.
                    ?url rdfs:label ?label.
                    ?url rdf:type <{query_type}>.
                    ?label <bif:contains> '({query_text})'.
                    FILTER (lang(?label) = {lang}).
                      }}    
                    }}
            }} ORDER BY strlen(str(?url)) LIMIT 3"""

        self.set_query(query)
        results = self.sparql.query().convert()
        if len(results["results"]["bindings"]) == 0:
          return []
        else:
          res_list=[]
          for res_dict in results["results"]["bindings"]:
              res_list.append(unquote(res_dict["url"]["value"]))
          return res_list


