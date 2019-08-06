<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:dyn="http://exslt.org/dynamic"
    xmlns:str="http://exslt.org/strings"
    extension-element-prefixes="dyn str"
    version="1.0">

  <xsl:param name="baseURL" />
  <xsl:param name="curDateTime" />
  <xsl:param name="courseID" />

  <xsl:include href="pylocal:html_to_markdown_2.xsl" />

  <xsl:preserve-space elements="*"/>

  <xsl:variable name="APOS">'</xsl:variable>

  <xsl:template name="mdHeading" mode="markdown">
    <xsl:param name="nodeName" />
    <xsl:param name="blockTitle" select="$nodeName"/>
    <xsl:param name="blockURL"/>
    <xsl:choose>
      <xsl:when test="$nodeName = 'course'"># </xsl:when>
      <xsl:when test="$nodeName = 'chapter'">## </xsl:when>
      <xsl:when test="$nodeName = 'sequential'">### </xsl:when>
      <xsl:when test="$nodeName = 'vertical'">#### </xsl:when>
      <xsl:otherwise>##### </xsl:otherwise>
    </xsl:choose>
    <xsl:choose>
      <xsl:when test="$blockURL">
        <xsl:value-of select="concat( '[', $blockTitle, '](', $blockURL, ') [', $blockURL, ']' )"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$blockTitle" />
      </xsl:otherwise>
    </xsl:choose><xsl:text>&#10;</xsl:text>
  </xsl:template>

  <xsl:template match="*">
    <xsl:apply-templates mode="markdown"/>
  </xsl:template>

  <xsl:template match="comment()"/>

  <!-- whitespace-only text node to explicit line break -->
  <xsl:template match="text()[not(normalize-space())]">
      <xsl:text>&#10;</xsl:text>
  </xsl:template>

<!-- TODO: 
[x] get text from custom node names
[x] handle verticals nodes with no url_name.... what attrs to pull out?
[x] handle code blocks
[x] get assets from json
[x] translate URLS for images and hrefs
[] maybe: don't reprint subheadings for verticals if same display_name as sequential
[x] handle <table> tags in html
[x] handle handouts
[x handle updates
[x] handle tabs
[x] handle custom xblocks
[x] don't include visible_to_staff_only blocks
[] maybe: wrap sequentials with prereqs prereq blocks with italics

-->  

<!-- root of XML to transform is the top-level course element (<course>) in course.xml -->
<!-- OLX export doesn't include a well-formed XML document with root -->
<!-- keep this (lack of) indentation -->
<xsl:template match="*[@course]">
<root>
<!-- the following 3 lines are used with the Pandoc yaml_metadata_block Markdown extension -->
---
title: <xsl:value-of select="dyn:evaluate('document(concat(&quot;tmpfs:course/&quot;, @url_name, &quot;.xml&quot;))')//course/@display_name"/>
date: Course exported from <xsl:value-of select="$baseURL" /> at <xsl:value-of select="$curDateTime" />
---
*<xsl:value-of select="$courseID"/>*
<xsl:text>&#10;</xsl:text>
<xsl:apply-templates select="document('tmpfs:about/overview.html')//section[@class='about']"/>
<xsl:apply-templates select="document('tmpfs:about/short_description.html')//section"/>
<xsl:apply-templates select="document('tmpfs:about/overview.html')//section[@class='prerequisites']"/>
<xsl:call-template name="updates"/>
<xsl:apply-templates select="dyn:evaluate('document(concat(&quot;tmpfs:course/&quot;, @url_name, &quot;.xml&quot;))')"/>
<xsl:apply-templates select="document('tabs:policies/course/policy.json')"/>
<xsl:call-template name="handouts"/>
<xsl:call-template name="assets"/>
</root>
</xsl:template>

  <!-- This excludes all staff only content.  Include/exclude would be a good configuration option candidate -->
  <xsl:template match="*[@visible_to_staff_only = 'true']" priority="2"/>

  <xsl:template match="course|chapter|sequential|vertical">
      <xsl:if test="local-name() != 'course'">
        <xsl:call-template name="mdHeading"><xsl:with-param name="nodeName" select="local-name()"/><xsl:with-param name="blockTitle" select="@display_name|@name"/><xsl:with-param name="blockURL" select="@href"/></xsl:call-template>
      </xsl:if>
      <xsl:apply-templates />
  </xsl:template>

  <xsl:template match="course/chapter[@url_name]">
    <xsl:apply-templates select="dyn:evaluate('document(concat(&quot;tmpfs:chapter/&quot;, @url_name, &quot;.xml&quot;))')"/>
  </xsl:template>

  <xsl:template match="chapter/sequential[@url_name]">
      <xsl:apply-templates select="dyn:evaluate('document(concat(&quot;tmpfs:sequential/&quot;, @url_name, &quot;.xml&quot;))')"/>
  </xsl:template>

  <xsl:template match="sequential/vertical[@url_name]">
      <xsl:apply-templates select="dyn:evaluate('document(concat(&quot;tmpfs:vertical/&quot;, @url_name, &quot;.xml&quot;))')"/>
  </xsl:template>

  <xsl:template match="vertical/*[not(self::html)][@url_name]" priority="2"><!-- resolve to file contents matching @url_name or if no file, match node -->
      <xsl:variable name="componentContents" select="dyn:evaluate('document(concat(&quot;tmpfs:&quot;, local-name(), &quot;/&quot;, @url_name, &quot;.xml&quot;))')"/>
      <xsl:choose>
        <xsl:when test="$componentContents/*"><!-- test for any content (url not resolved as empty) -->
          <xsl:apply-templates select="$componentContents" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="nonFileComponent" mode="markdown">
            <xsl:with-param name="nodeType" select="local-name()"/>
            <xsl:with-param name="displayName" select="@display_name|@name" />
          </xsl:call-template>           
        </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="vertical/html[@url_name]">
    <xsl:apply-templates select="dyn:evaluate('document(concat(&quot;tmpfs:html/&quot;, @url_name, &quot;.xml&quot;))')" />
  </xsl:template>

  <xsl:template match="html[@filename]" priority="2"><!-- process the actual .html file for html components -->
    <xsl:apply-templates select="dyn:evaluate('document(concat(&quot;tmpfs:html/&quot;, @filename, &quot;.html&quot;))')"/>
  </xsl:template>

  <!-- make sure to at least display a heading for any other component type -->
  <xsl:template match="*[@display_name|@name]" priority="1">
    <xsl:call-template name="mdHeading" mode="markdown">
      <xsl:with-param name="nodeName" select="local-name()"/>
      <xsl:with-param name="blockURL" select="@href"/>
      <xsl:with-param name="blockTitle" select="@display_name|@name"/>
    </xsl:call-template>
    <xsl:apply-templates/>
  </xsl:template>


  <!-- CUSTOM COMPONENT NODES -->
  
<xsl:template name="nonFileComponent" mode="markdown"><!-- print out the name or node name and field values -->
  <xsl:param name="nodeType"/>
  <xsl:param name="displayName"/>
  <xsl:call-template name="mdHeading" mode="markdown">
    <xsl:with-param name="nodeName" select="$nodeType"/>
    <xsl:with-param name="blockURL" select="@href"/>
    <xsl:with-param name="blockTitle" select="$displayName"/>
  </xsl:call-template>
<xsl:for-each select="@*[not(name() = 'display_name' or name() = 'name' or name() = 'url_name' or name() = 'xblock-family' or name() = 'markdown')]">
<xsl:value-of select="concat('*', local-name(), ':* ', current())" /><xsl:text>&#10;</xsl:text>
</xsl:for-each>
</xsl:template>


<xsl:template match="video/source" mode="markdown"><!-- all the information is in attrs -->
  video source [<xsl:value-of select="@src" />](<xsl:value-of select="@src" />))
</xsl:template>

<xsl:template name="choiceCorrectness" mode="markdown">
  <xsl:choose>
    <xsl:when test="@correct = 'true'">x</xsl:when>
    <xsl:otherwise><xsl:text> </xsl:text></xsl:otherwise> 
  </xsl:choose>
</xsl:template>

<!-- TODO: fix this -->
<xsl:template match="optionresponse|choicegroup" mode="markdown">
  <xsl:apply-templates/>
  <xsl:text>&#10;</xsl:text>
</xsl:template>

<xsl:template match="multiplechoiceresponse//choice" mode="markdown">
  - [<xsl:call-template name="choiceCorrectness"/>] <xsl:value-of select="./text()" />
</xsl:template>

<xsl:template match="optionresponse//optioninput" mode="markdown">
  <!-- like <optioninput options="('yellow','blue','green')" correct="blue"/> -->
  <xsl:variable name="correctOptionVal"><xsl:value-of select="@correct"/></xsl:variable>
  <xsl:for-each select="str:split(translate(translate(@options, '()', ''), $APOS, ''), ',')">
    <xsl:choose>
      <xsl:when test="text() = $correctOptionVal">
      - [x] <xsl:value-of select="current()" />
      </xsl:when>
      <xsl:otherwise>
      - [ ] <xsl:value-of select="current()" />
      </xsl:otherwise>
    </xsl:choose>  
  </xsl:for-each>
</xsl:template>

<!-- don't output scripts used in answer eval -->
<xsl:template match="problem//script|answer[@type='loncapa/python']" />

<xsl:template 

<xsl:template name="updates" mode="markdown">
<xsl:text>----

### Course Updates and News

</xsl:text>
<xsl:apply-templates select="document('tmpfs:info/updates.html')" />
</xsl:template>

<xsl:template name="handouts" mode="markdown">
<xsl:text>----

### Handouts

</xsl:text>
<xsl:apply-templates select="document('tmpfs:info/handouts.html')" />
</xsl:template>

<xsl:template name="assets" mode="markdown">
<!-- output parsed assets JSON file -->
<xsl:text>----
----

### Assets

</xsl:text>
<xsl:value-of select="document('assets:policies/assets.json')" />
</xsl:template>

</xsl:stylesheet>
