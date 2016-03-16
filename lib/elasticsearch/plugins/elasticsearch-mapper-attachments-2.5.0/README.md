Mapper Attachments Type for Elasticsearch
=========================================

The mapper attachments plugin adds the `attachment` type to Elasticsearch using [Apache Tika](http://lucene.apache.org/tika/).
The `attachment` type allows to index different "attachment" type field (encoded as `base64`), for example,
microsoft office formats, open document formats, ePub, HTML, and so on (full list can be found [here](http://tika.apache.org/1.5/formats.html)).

## Version 2.5.0 for Elasticsearch: 1.5

If you are looking for another version documentation, please refer to the 
[compatibility matrix](https://github.com/elasticsearch/elasticsearch-mapper-attachments/#mapper-attachments-type-for-elasticsearch).


Using mapper attachments
------------------------

Using the attachment type is simple, in your mapping JSON, simply set a certain JSON element as attachment, for example:

```javascript
PUT /test/person/_mapping
{
    "person" : {
        "properties" : {
            "my_attachment" : { "type" : "attachment" }
        }
    }
}
```

In this case, the JSON to index can be:

```javascript
PUT /test/person/1
{
    "my_attachment" : "... base64 encoded attachment ..."
}
```

Or it is possible to use more elaborated JSON if content type, resource name or language need to be set explicitly:

```
PUT /test/person/1
{
    "my_attachment" : {
        "_content_type" : "application/pdf",
        "_name" : "resource/name/of/my.pdf",
        "_language" : "en",
        "_content" : "... base64 encoded attachment ..."
    }
}
```

The `attachment` type not only indexes the content of the doc, but also automatically adds meta data on the attachment 
as well (when available).

The metadata supported are:

* `date`
* `title`
* `name` only available if you set `_name` see above
* `author`
* `keywords`
* `content_type`
* `content_length` is the original content_length before text extraction (aka file size)
* `language`

They can be queried using the "dot notation", for example: `my_attachment.author`.

Both the meta data and the actual content are simple core type mappers (string, date, ...), thus, they can be controlled 
in the mappings. For example:

```javascript
PUT /test/person/_mapping
{
    "person" : {
        "properties" : {
            "file" : {
                "type" : "attachment",
                "fields" : {
                    "file" : {"index" : "no"},
                    "title" : {"store" : "yes"},
                    "date" : {"store" : "yes"},
                    "author" : {"analyzer" : "myAnalyzer"},
                    "keywords" : {"store" : "yes"},
                    "content_type" : {"store" : "yes"},
                    "content_length" : {"store" : "yes"},
                    "language" : {"store" : "yes"}
                }
            }
        }
    }
}
```

In the above example, the actual content indexed is mapped under `fields` name `file`, and we decide not to index it, so 
it will only be available in the `_all` field. The other fields map to their respective metadata names, but there is no 
need to specify the `type` (like `string` or `date`) since it is already known.

Copy To feature
---------------

If you want to use [copy_to](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/mapping-core-types.html#copy-to)
feature, you need to define it on each sub-field you want to copy to another field:

```javascript
PUT /test/person/_mapping
{
  "person": {
    "properties": {
      "file": {
        "type": "attachment",
        "path": "full",
        "fields": {
          "file": {
            "type": "string",
            "copy_to": "copy"
          }
        }
      },
      "copy": {
        "type": "string"
      }
    }
  }
}
```

In this example, the extracted content will be copy as well to `copy` field.

Querying or accessing metadata
------------------------------

If you need to query on metadata fields, use the attachment field name dot the metadata field. For example:

```
DELETE /test
PUT /test
PUT /test/person/_mapping
{
  "person": {
    "properties": {
      "file": {
        "type": "attachment",
        "path": "full",
        "fields": {
          "content_type": {
            "type": "string",
            "store": true
          }
        }
      }
    }
  }
}
PUT /test/person/1?refresh=true
{
  "file": "IkdvZCBTYXZlIHRoZSBRdWVlbiIgKGFsdGVybmF0aXZlbHkgIkdvZCBTYXZlIHRoZSBLaW5nIg=="
}
GET /test/person/_search
{
  "fields": [ "file.content_type" ], 
  "query": {
    "match": {
      "file.content_type": "text plain"
    }
  }
}
```

Will give you:

```
{
   "took": 2,
   "timed_out": false,
   "_shards": {
      "total": 5,
      "successful": 5,
      "failed": 0
   },
   "hits": {
      "total": 1,
      "max_score": 0.16273327,
      "hits": [
         {
            "_index": "test",
            "_type": "person",
            "_id": "1",
            "_score": 0.16273327,
            "fields": {
               "file.content_type": [
                  "text/plain; charset=ISO-8859-1"
               ]
            }
         }
      ]
   }
}
```

Indexed Characters
------------------

By default, `100000` characters are extracted when indexing the content. This default value can be changed by setting 
the `index.mapping.attachment.indexed_chars` setting. It can also be provided on a per document indexed using the 
`_indexed_chars` parameter. `-1` can be set to extract all text, but note that all the text needs to be allowed to be 
represented in memory:

```
PUT /test/person/1
{
    "my_attachment" : {
        "_indexed_chars" : -1,
        "_content" : "... base64 encoded attachment ..."
    }
}
```

Metadata parsing error handling
-------------------------------

While extracting metadata content, errors could happen for example when parsing dates.
Parsing errors are ignored so your document is indexed.

You can disable this feature by setting the `index.mapping.attachment.ignore_errors` setting to `false`.

Language Detection
------------------

By default, language detection is disabled (`false`) as it could come with a cost.
This default value can be changed by setting the `index.mapping.attachment.detect_language` setting.
It can also be provided on a per document indexed using the `_detect_language` parameter.

Note that you can force language using `_language` field when sending your actual document:

```javascript
{
    "my_attachment" : {
        "_language" : "en",
        "_content" : "... base64 encoded attachment ..."
    }
}
```

Highlighting attachments
------------------------

If you want to highlight your attachment content, you will need to set `"store": true` and `"term_vector":"with_positions_offsets"`
for your attachment field. Here is a full script which does it:

```
DELETE /test
PUT /test
PUT /test/person/_mapping
{
  "person": {
    "properties": {
      "file": {
        "type": "attachment",
        "path": "full",
        "fields": {
          "file": {
            "type": "string",
            "term_vector":"with_positions_offsets",
            "store": true
          }
        }
      }
    }
  }
}
PUT /test/person/1?refresh=true
{
  "file": "IkdvZCBTYXZlIHRoZSBRdWVlbiIgKGFsdGVybmF0aXZlbHkgIkdvZCBTYXZlIHRoZSBLaW5nIg=="
}
GET /test/person/_search
{
  "fields": [], 
  "query": {
    "match": {
      "file": "king queen"
    }
  },
  "highlight": {
    "fields": {
      "file": {
      }
    }
  }
}
```

It gives back:

```js
{
   "took": 9,
   "timed_out": false,
   "_shards": {
      "total": 1,
      "successful": 1,
      "failed": 0
   },
   "hits": {
      "total": 1,
      "max_score": 0.13561106,
      "hits": [
         {
            "_index": "test",
            "_type": "person",
            "_id": "1",
            "_score": 0.13561106,
            "highlight": {
               "file": [
                  "\"God Save the <em>Queen</em>\" (alternatively \"God Save the <em>King</em>\"\n"
               ]
            }
         }
      ]
   }
}
```

Stand alone runner
------------------

If you want to run some tests within your IDE, you can use `StandaloneRunner` class.
It accepts arguments:

*  `-u file://URL/TO/YOUR/DOC`
*  `--size` set extracted size (default to mapper attachment size)
*  `BASE64` encoded binary

Example:

```sh
StandaloneRunner BASE64Text
StandaloneRunner -u /tmp/mydoc.pdf
StandaloneRunner -u /tmp/mydoc.pdf --size 1000000
```

It produces something like:

```
## Extracted text
--------------------- BEGIN -----------------------
This is the extracted text
---------------------- END ------------------------
## Metadata
- author: null
- content_length: null
- content_type: application/pdf
- date: null
- keywords: null
- language: null
- name: null
- title: null
```

License
-------

    This software is licensed under the Apache 2 license, quoted below.

    Copyright 2009-2014 Elasticsearch <http://www.elasticsearch.org>

    Licensed under the Apache License, Version 2.0 (the "License"); you may not
    use this file except in compliance with the License. You may obtain a copy of
    the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations under
    the License.
