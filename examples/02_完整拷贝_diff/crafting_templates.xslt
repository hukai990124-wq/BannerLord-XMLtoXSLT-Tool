<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns="">
  <xsl:output omit-xml-declaration="no" indent="yes" />
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()" />
    </xsl:copy>
  </xsl:template>
  <xsl:template match="/CraftingTemplates[1]/CraftingTemplate[@id='OneHandedSword']/UsablePieces[1]">
    <xsl:copy>
      <xsl:copy-of select="@*" />
      <xsl:apply-templates select="node()" />
      <xsl:element name="UsablePiece">
        <xsl:attribute name="piece_id">example_blade_a</xsl:attribute>
      </xsl:element>
      <xsl:element name="UsablePiece">
        <xsl:attribute name="piece_id">example_blade_b</xsl:attribute>
      </xsl:element>
      <xsl:element name="UsablePiece">
        <xsl:attribute name="piece_id">example_handle_a</xsl:attribute>
      </xsl:element>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="/CraftingTemplates[1]/CraftingTemplate[@id='OneHandedSword']">
    <xsl:copy>
      <xsl:copy-of select="@*" />
      <xsl:attribute name="modifier_group">example_sword_group</xsl:attribute>
      <xsl:apply-templates select="node()" />
    </xsl:copy>
  </xsl:template>
</xsl:stylesheet>
