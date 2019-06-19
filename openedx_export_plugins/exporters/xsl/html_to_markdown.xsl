<?xml version="1.0" encoding="UTF-8"?>
<!-- adapted to XSL 1from https://gist.github.com/gabetax/1702774 -->
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:functx="http://www.functx.com"
    xmlns:xs="http://www.w3.org/2001/XMLSchema" 
    version="1.0">
    
  <xsl:output method="text" indent="no"/>
  <xsl:preserve-space elements="*" />

  <!-- Required for li indenting -->
<!--   <xsl:function name="functx:repeat-string" as="xs:string">
    <xsl:param name="stringToRepeat" as="xs:string?"/> 
    <xsl:param name="count" as="xs:integer"/> 
    <xsl:sequence select="string-join((for $i in 1 to $count return $stringToRepeat), '')"/>
  </xsl:function> -->

  <xsl:template match="*">
    <xsl:apply-templates select="*" />
  </xsl:template>

<!--   <xsl:template match="li">
    <xsl:value-of select="functx:repeat-string('    ', count(ancestor::li))"/>
    <xsl:choose>
      <xsl:when test="name(..) = 'ol'">
        <xsl:value-of select="position()" />
        <xsl:text>. </xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>* </xsl:text>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:value-of select="normalize-space(text())" />
    <xsl:apply-templates select="* except (ul|ol)" />
    <xsl:text>&#xa;&#xa;</xsl:text>
    <xsl:apply-templates select="ul|ol" />
  </xsl:template> -->

  <!-- Don't process text() nodes for these - prevents unnecessary whitespace -->
  <xsl:template match="ul|ol">
    <xsl:apply-templates select="node()" />
  </xsl:template>

  <xsl:template match="a">
    <xsl:text>[</xsl:text>
    <xsl:apply-templates select="node()|text()" />
    <xsl:text>](</xsl:text>
    <xsl:value-of select="@href" />
    <xsl:text>)</xsl:text>
  </xsl:template>

  <xsl:template match="img|imageinput">
    <xsl:text>![</xsl:text>
    <xsl:value-of select="@alt" />
    <xsl:text>](</xsl:text>
    <xsl:value-of select="@src" />
    <xsl:text>)</xsl:text>
  </xsl:template>


  <xsl:template match="strong|b">
    <xsl:text>**</xsl:text>
    <xsl:value-of select="." />
    <xsl:text>**</xsl:text>
  </xsl:template>
  <xsl:template match="em|i">
    <xsl:text>*</xsl:text>
    <xsl:value-of select="." />
    <xsl:text>*</xsl:text>
  </xsl:template>
  <xsl:template match="code">
    <!-- todo: skip the ` if inside a pre -->
    <xsl:text>`</xsl:text>
    <xsl:value-of select="." />
    <xsl:text>`</xsl:text>
  </xsl:template>

  <xsl:template match="br">
    <xsl:text>  &#xa;</xsl:text>
  </xsl:template>
  
  <!-- Block elements -->
  <xsl:template match="hr">
    <xsl:text>----&#xa;&#xa;</xsl:text>
  </xsl:template>
  
  <xsl:template match="p|div">
    <xsl:apply-templates select="*|text()" />
    <xsl:text>&#xa;&#xa;</xsl:text> <!-- Block element -->
  </xsl:template>
  
  <xsl:template match="h1">##<xsl:text> </xsl:text><xsl:apply-templates select="*|text()" /></xsl:template>
  <xsl:template match="h2">###<xsl:text> </xsl:text><xsl:apply-templates select="*|text()" /></xsl:template>
  <xsl:template match="h3">####<xsl:text> </xsl:text><xsl:apply-templates select="*|text()" /></xsl:template>
  <xsl:template match="h4">#####<xsl:text> </xsl:text><xsl:apply-templates select="*|text()" /></xsl:template>
  <xsl:template match="h5">######<xsl:text> </xsl:text><xsl:apply-templates select="*|text()" /></xsl:template>
  <xsl:template match="h6">#######<xsl:text> </xsl:text><xsl:apply-templates select="*|text()" /></xsl:template>  
  

</xsl:stylesheet>