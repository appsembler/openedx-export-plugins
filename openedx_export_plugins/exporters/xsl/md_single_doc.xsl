<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:dyn="http://exslt.org/dynamic"
    extension-element-prefixes="dyn"
    version="1.0">

  <xsl:include href="pylocal:html_to_markdown.xsl" />
  <xsl:output method="text" encoding="utf-8" indent="no"/>
  <xsl:preserve-space elements="*"/>


  <xsl:template name="mdHeading">
    <xsl:param name="nodeName" />
    <xsl:param name="blockTitle"><xsl:value-of select="$nodeName"/></xsl:param>
    <xsl:param name="blockURL"></xsl:param>
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
    <xsl:apply-templates />
  </xsl:template>

  <xsl:template match="comment()"/>

  <xsl:template match="//text()">
    <xsl:value-of select="translate(., '#', '`#`')" />
    <xsl:apply-templates />
  </xsl:template>

  <!-- whitespace-only text node to explicit line break -->
  <xsl:template match="text()[not(normalize-space())]">
      <xsl:text>&#10;</xsl:text>
  </xsl:template>

<!-- TODO: 
[x] get text from custom node names
[x] handle verticals nodes with no url_name.... what attrs to pull out?
[x] handle code blocks
[x] get assets from json
[-] translate URLS for images and hrefs
[] maybe: don't reprint subheadings for verticals if same display_name as sequential
[] handle <table> tags in html
[x] handle handouts
[x handle updates
[x] handle tabs
[] handle custom xblocks
[] wrap visible_to_staff_only blocks with italics
[] wrap sequentials with prereqs prereq blocks with italics

-->  

<!-- root of XML to transform is the top-level course element (<course>) in course.xml -->
<!-- OLX export doesn't include a well-formed XML document with root -->
<!-- keep this (lack of) indentation -->
<xsl:template match="*[@course]">
<root>
# <xsl:value-of select="dyn:evaluate('document(concat(&quot;tmpfs:course/&quot;, @url_name, &quot;.xml&quot;))')//course/@display_name"/>
*<xsl:value-of select="./@org"/> / <xsl:value-of select="./@course"/> / <xsl:value-of select="./@url_name"/>*
<xsl:apply-templates select="document('tmpfs:about/overview.html')//section[@class='about']"/>
<xsl:apply-templates select="document('tmpfs:about/short_description.html')//section"/>
<xsl:apply-templates select="document('tmpfs:about/overview.html')//section[@class='prerequisites']"/>
<xsl:call-template name="updates"/>
<xsl:apply-templates select="dyn:evaluate('document(concat(&quot;tmpfs:course/&quot;, @url_name, &quot;.xml&quot;))')"/>
<xsl:apply-templates select="document('tabs:policies/course/policy.json')"/>
<xsl:call-template name="handouts"/>
<!-- <xsl:call-template name="assets"/> -->
</root>
</xsl:template>

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

  <xsl:template match="vertical/*[@url_name]"><!-- resolve to file contents matching @url_name or if no file, match node -->
      <xsl:if test="local-name() != 'html'">
        <xsl:call-template name="nonFileComponent">
          <xsl:with-param name="nodeType"><xsl:value-of select="local-name()" /></xsl:with-param>
        </xsl:call-template> 
      </xsl:if>
      <xsl:apply-templates select="dyn:evaluate('document(concat(&quot;tmpfs:&quot;, local-name(), &quot;/&quot;, @url_name, &quot;.xml&quot;))')" />
<!--      <xsl:variable name="componentFile" select="dyn:evaluate('document(concat(&quot;tmpfs:&quot;, local-name(), &quot;/&quot;, @url_name, &quot;.xml&quot;))')" />
      path: <xsl:value-of select="concat(&quot;tmpfs:&quot;, local-name(), &quot;/&quot;, @url_name, &quot;.xml&quot;)"/>
      componentFile: <xsl:value-of select="$componentFile" />foo <xsl:text>&#10;</xsl:text>

       <xsl:choose>
        <xsl:when test="$componentFile">
          <xsl:apply-templates select="$componentFile" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="nonFileComponent">
            <xsl:with-param name="nodeType"><xsl:value-of select="local-name()" /></xsl:with-param>
          </xsl:call-template> 
        </xsl:otherwise>
      </xsl:choose>
 -->      

  </xsl:template>

  <xsl:template match="html[@filename]"><!-- process the actual .html file for html components -->
    <xsl:apply-templates select="dyn:evaluate('document(concat(&quot;tmpfs:html/&quot;, @filename, &quot;.html&quot;))')"/>
  </xsl:template>

  <!-- CUSTOM COMPONENT NODES -->

  
<xsl:template name="nonFileComponent"><!-- print out the name or node name and field values -->
  <xsl:param name="nodeType"/>
  <xsl:variable name="displayName" select="@display_name|@name" />
  <xsl:call-template name="mdHeading"><xsl:with-param name="nodeName" select="$nodeType"/><xsl:with-param name="blockURL" select="@href"/></xsl:call-template>
  <xsl:for-each select="@*[not(name() = 'display_name' or name() = 'name' or name() = 'url_name' or name() = 'xblock-family')]">
* <xsl:value-of select="concat(local-name(), ': ', current())" /><xsl:text>&#10;</xsl:text>
  </xsl:for-each>
</xsl:template>


<xsl:template match="video/source"><!-- all the information is in attrs -->
  video source [<xsl:value-of select="@src" />](<xsl:value-of select="@src" />))
</xsl:template>  

<xsl:template match="multiplechoiceresponse//choice">
  <xsl:text>* [ ] </xsl:text> <xsl:value-of select="./text()" />
</xsl:template>

<xsl:template match="optionresponse//optioninput/@options">
  <xsl:text>* [ ] </xsl:text> <xsl:value-of select="." /><!-- TODO:split the py string -->
</xsl:template>

<!-- don't output scripts used in answer eval -->
<xsl:template match="problem//script|answer[@type='loncapa/python']" />

<!-- <xsl:template match="html//table">[HTML TABLE not displayed]</xsl:template> --><!-- drop tables for now -->



<xsl:template name="updates">
<xsl:text>----
### UPDATES

</xsl:text>
<xsl:apply-templates select="document('tmpfs:info/updates.html')" />
</xsl:template>

<xsl:template name="handouts">
<xsl:text>----
### HANDOUTS

</xsl:text>
<xsl:apply-templates select="document('tmpfs:info/handouts.html')" />
</xsl:template>

<xsl:template name="assets">
<!-- output parsed assets JSON file -->
<xsl:text>----
----
### ASSETS

</xsl:text>
<xsl:value-of select="document('assets:policies/assets.json')" />
</xsl:template>

</xsl:stylesheet>
