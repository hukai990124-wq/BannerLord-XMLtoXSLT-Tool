<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns="">
  <xsl:output omit-xml-declaration="no" indent="yes" />
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()" />
    </xsl:copy>
  </xsl:template>
  <xsl:template match="/CraftingTemplates[1]">
    <xsl:copy>
      <xsl:copy-of select="@*" />
      <xsl:apply-templates select="node()" />

      <xsl:element name="CraftingTemplate">
        <xsl:attribute name="id">mv_tribune_template</xsl:attribute>
        <xsl:attribute name="item_type">OneHandedWeapon</xsl:attribute>
        <xsl:attribute name="modifier_group">sword</xsl:attribute>
        <xsl:attribute name="item_holsters">sword_left_hip_3:sword_left_hip:sword_left_hip_2:sword_back</xsl:attribute>
        <xsl:attribute name="default_item_holster_position_offset">0,0,-0.1</xsl:attribute>
        <xsl:attribute name="use_weapon_as_holster_mesh">true</xsl:attribute>
        <xsl:element name="PieceDatas">
          <xsl:element name="PieceData">
            <xsl:attribute name="piece_type">Blade</xsl:attribute>
            <xsl:attribute name="build_order">0</xsl:attribute>
          </xsl:element>
        </xsl:element>
        <xsl:element name="WeaponDescriptions">
          <xsl:element name="WeaponDescription">
            <xsl:attribute name="id">mv_tribune_description</xsl:attribute>
          </xsl:element>
        </xsl:element>
        <xsl:element name="StatsData">
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">Weight</xsl:attribute>
            <xsl:attribute name="max_value">7.0</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">WeaponReach</xsl:attribute>
            <xsl:attribute name="max_value">300</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">ThrustSpeed</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">SwingSpeed</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">ThrustDamage</xsl:attribute>
            <xsl:attribute name="max_value">500</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">SwingDamage</xsl:attribute>
            <xsl:attribute name="max_value">500</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">Handling</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
        </xsl:element>
        <xsl:element name="UsablePieces">
          <xsl:element name="UsablePiece">
            <xsl:attribute name="piece_id">mv_tribune_piece</xsl:attribute>
          </xsl:element>
        </xsl:element>
      </xsl:element>

      <xsl:element name="CraftingTemplate">
        <xsl:attribute name="id">mv_lictor_template</xsl:attribute>
        <xsl:attribute name="item_type">TwoHandedWeapon</xsl:attribute>
        <xsl:attribute name="modifier_group">axe</xsl:attribute>
        <xsl:attribute name="item_holsters">axe_back:axe_back_2:axe_back_3:axe_back_4</xsl:attribute>
        <xsl:attribute name="default_item_holster_position_offset">0,0,-0.65</xsl:attribute>
        <xsl:attribute name="use_weapon_as_holster_mesh">true</xsl:attribute>
        <xsl:element name="PieceDatas">
          <xsl:element name="PieceData">
            <xsl:attribute name="piece_type">Blade</xsl:attribute>
            <xsl:attribute name="build_order">0</xsl:attribute>
          </xsl:element>
        </xsl:element>
        <xsl:element name="WeaponDescriptions">
          <xsl:element name="WeaponDescription">
            <xsl:attribute name="id">mv_lictor_description</xsl:attribute>
          </xsl:element>
        </xsl:element>
        <xsl:element name="StatsData">
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">Weight</xsl:attribute>
            <xsl:attribute name="max_value">7.0</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">WeaponReach</xsl:attribute>
            <xsl:attribute name="max_value">300</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">ThrustSpeed</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">SwingSpeed</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">ThrustDamage</xsl:attribute>
            <xsl:attribute name="max_value">500</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">SwingDamage</xsl:attribute>
            <xsl:attribute name="max_value">500</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">Handling</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
        </xsl:element>
        <xsl:element name="UsablePieces">
          <xsl:element name="UsablePiece">
            <xsl:attribute name="piece_id">mv_lictor_piece</xsl:attribute>
          </xsl:element>
        </xsl:element>
      </xsl:element>

      <xsl:element name="CraftingTemplate">
        <xsl:attribute name="id">mv_dominus_template</xsl:attribute>
        <xsl:attribute name="item_type">Polearm</xsl:attribute>
        <xsl:attribute name="modifier_group">polearm</xsl:attribute>
        <xsl:attribute name="item_holsters">polearm_back:polearm_back_2:polearm_back_3:polearm_back_4</xsl:attribute>
        <xsl:attribute name="default_item_holster_position_offset">0,0,-0.65</xsl:attribute>
        <xsl:attribute name="use_weapon_as_holster_mesh">true</xsl:attribute>
        <xsl:element name="PieceDatas">
          <xsl:element name="PieceData">
            <xsl:attribute name="piece_type">Blade</xsl:attribute>
            <xsl:attribute name="build_order">0</xsl:attribute>
          </xsl:element>
        </xsl:element>
        <xsl:element name="WeaponDescriptions">
          <xsl:element name="WeaponDescription">
            <xsl:attribute name="id">mv_dominus_description</xsl:attribute>
          </xsl:element>
        </xsl:element>
        <xsl:element name="StatsData">
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">Weight</xsl:attribute>
            <xsl:attribute name="max_value">7.0</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">WeaponReach</xsl:attribute>
            <xsl:attribute name="max_value">300</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">ThrustSpeed</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">SwingSpeed</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">ThrustDamage</xsl:attribute>
            <xsl:attribute name="max_value">500</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">SwingDamage</xsl:attribute>
            <xsl:attribute name="max_value">500</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">Handling</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
        </xsl:element>
        <xsl:element name="UsablePieces">
          <xsl:element name="UsablePiece">
            <xsl:attribute name="piece_id">mv_dominus_piece</xsl:attribute>
          </xsl:element>
        </xsl:element>
      </xsl:element>

      <xsl:element name="CraftingTemplate">
        <xsl:attribute name="id">mv_domina_template</xsl:attribute>
        <xsl:attribute name="item_type">Polearm</xsl:attribute>
        <xsl:attribute name="modifier_group">polearm</xsl:attribute>
        <xsl:attribute name="item_holsters">polearm_back:polearm_back_2:polearm_back_3:polearm_back_4</xsl:attribute>
        <xsl:attribute name="default_item_holster_position_offset">0,0,-0.65</xsl:attribute>
        <xsl:attribute name="use_weapon_as_holster_mesh">true</xsl:attribute>
        <xsl:element name="PieceDatas">
          <xsl:element name="PieceData">
            <xsl:attribute name="piece_type">Blade</xsl:attribute>
            <xsl:attribute name="build_order">0</xsl:attribute>
          </xsl:element>
        </xsl:element>
        <xsl:element name="WeaponDescriptions">
          <xsl:element name="WeaponDescription">
            <xsl:attribute name="id">mv_domina_one_handed_description</xsl:attribute>
          </xsl:element>
          <xsl:element name="WeaponDescription">
            <xsl:attribute name="id">mv_domina_two_handed_description</xsl:attribute>
          </xsl:element>
          <xsl:element name="WeaponDescription">
            <xsl:attribute name="id">mv_domina_couchable_description</xsl:attribute>
          </xsl:element>
        </xsl:element>
        <xsl:element name="StatsData">
          <xsl:attribute name="weapon_description">mv_domina_one_handed_description</xsl:attribute>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">Weight</xsl:attribute>
            <xsl:attribute name="max_value">7.0</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">WeaponReach</xsl:attribute>
            <xsl:attribute name="max_value">300</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">ThrustSpeed</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">SwingSpeed</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">ThrustDamage</xsl:attribute>
            <xsl:attribute name="max_value">500</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">SwingDamage</xsl:attribute>
            <xsl:attribute name="max_value">500</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">Handling</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
        </xsl:element>
        <xsl:element name="StatsData">
          <xsl:attribute name="weapon_description">mv_domina_two_handed_description</xsl:attribute>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">Weight</xsl:attribute>
            <xsl:attribute name="max_value">7.0</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">WeaponReach</xsl:attribute>
            <xsl:attribute name="max_value">300</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">ThrustSpeed</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">SwingSpeed</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">ThrustDamage</xsl:attribute>
            <xsl:attribute name="max_value">500</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">SwingDamage</xsl:attribute>
            <xsl:attribute name="max_value">500</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">Handling</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
        </xsl:element>
        <xsl:element name="StatsData">
          <xsl:attribute name="weapon_description">mv_domina_couchable_description</xsl:attribute>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">Weight</xsl:attribute>
            <xsl:attribute name="max_value">7.0</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">WeaponReach</xsl:attribute>
            <xsl:attribute name="max_value">300</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">ThrustSpeed</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">SwingSpeed</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">ThrustDamage</xsl:attribute>
            <xsl:attribute name="max_value">500</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">SwingDamage</xsl:attribute>
            <xsl:attribute name="max_value">500</xsl:attribute>
          </xsl:element>
          <xsl:element name="StatData">
            <xsl:attribute name="stat_type">Handling</xsl:attribute>
            <xsl:attribute name="max_value">200</xsl:attribute>
          </xsl:element>
        </xsl:element>
        <xsl:element name="UsablePieces">
          <xsl:element name="UsablePiece">
            <xsl:attribute name="piece_id">mv_domina_piece</xsl:attribute>
          </xsl:element>
        </xsl:element>
      </xsl:element>
    </xsl:copy>
  </xsl:template>
</xsl:stylesheet>
