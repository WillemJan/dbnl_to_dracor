# Jinja2 template
# https://jinja.palletsprojects.com/en/3.1.x/templates/

xml_template = """<?xml version="1.0" encoding="utf-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="{xml_id}" xml:lang="nl">
  <fileDesc>
    <titleStmt>
      <title type="main">{main_title}</title>
      <title type="sub">{sub_title}</title>
      <author>
        <persName>
          <forename>author name</forename>
          <surname>author surname</surname>
        </persName>
        <idno type="wikidata">wikidata identifier</idno>
        <idno type="pnd">pnd identifier (optional)</idno>
      </author>
    </titleStmt>
    <publicationStmt>
      <publisher xml:id="dracor">DraCor</publisher>
      <idno type="URL">https://dracor.org</idno>
      <availability>
        <licence>
          <ab>CC0 1.0</ab>
          <ref target="https://creativecommons.org/publicdomain/zero/1.0/">Licence</ref>
        </licence>
      </availability>
    </publicationStmt>
    <sourceDesc>
      <bibl type="digitalSource">
        <name>name of source here</name>
        <idno type="URL">url here</idno>
        <availability status="free">
          <p>In the public domain.</p>
        </availability>
        <bibl type="originalSource">
          <title>Autor: Title. Place: Publisher, 0000.</title>
        </bibl>
      </bibl>
    </sourceDesc>
  </fileDesc>
  <profileDesc>
    <particDesc>
      <listPerson>
        <person xml:id="person-id" sex="m/f/u">
          <persName>character name</persName>
        </person>
        <personGrp xml:id="group-id" sex="m/f/u">
          <name>group name</name>
        </personGrp>
        <listRelation type="type of relation">
          <relation name="" active="pers_1" passive="pers_2"/>
        </listRelation>
      </listPerson>
    </particDesc>
    <textClass>
      <keywords>
        <term type="genreTitle">name of genre</term>
      </keywords>
    </textClass>
  </profileDesc>
  <revisionDesc>
    <listChange>
      <change when="0000-00-00">who did what</change>
    </listChange>
  </revisionDesc>
  <standOff>
    <listEvent>
      <event type="print" when="yyyy">
        <desc/>
      </event>
      <event type="premiere" when="">
        <desc/>
      </event>
      <event type="written" when="">
        <desc/>
      </event>
    </listEvent>
    <listRelation>
      <relation name="wikidata" active="https://dracor.org/entity/" passive="http://www.wikidata.org/entity/"/>
    </listRelation>
  </standOff>
  <text>
    <front>
      <head/>
      <castList>
	  </castList>
      <set>
        <p>Setting</p>
      </set>
    </front>
  </text>
</TEI>
"""


