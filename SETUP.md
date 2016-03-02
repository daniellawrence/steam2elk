SETUP
-------

Running

```
python ./tf2.py -e 'http://8fa239f0e05aa55efb668571bccf308.us-west-1.aws.found.io:9200/index_tf2/type_kill/'
```

Setting up the indexs

```
PUT /index_tf2
{
  "mappings": {
    "type_kill": {
        "dynamic_templates": [
            { "notanalyzed": {
                  "match":              "*", 
                  "match_mapping_type": "string",
                  "mapping": {
                      "type":        "string",
                      "index":       "not_analyzed"
                  }
               }
            }
          ]
       }
   }
}
```
