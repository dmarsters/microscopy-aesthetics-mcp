"""
tests/test_server.py - Unit tests for microscopy-aesthetics-mcp server
"""

import pytest
from microscopy_aesthetics.server import (
    MICROSCOPY_PROFILES,
    enhance_prompt_with_microscopy,
    list_microscopy_types,
    get_microscopy_profile,
    suggest_microscopy_type,
)


class TestProfileStructure:
    """Test that all profiles have required structure."""
    
    def test_all_profiles_present(self):
        """Test that all 7 microscopy types are defined."""
        expected_types = {
            'fluorescence', 'electron', 'phase_contrast', 'confocal',
            'brightfield', 'darkfield', 'multiphoton'
        }
        assert set(MICROSCOPY_PROFILES.keys()) == expected_types
    
    def test_profile_completeness(self):
        """Test that all profiles have required fields."""
        required_fields = {
            'display_name', 'description', 'structure', 'material',
            'color', 'texture', 'composition', 'style', 'quality',
            'mood', 'examples', 'color_palette', 'magnification_feel'
        }
        
        for typename, profile in MICROSCOPY_PROFILES.items():
            missing_fields = required_fields - set(profile.keys())
            assert not missing_fields, f"{typename} missing fields: {missing_fields}"
    
    def test_magnification_levels(self):
        """Test that all magnification levels are defined."""
        expected_levels = {'low', 'medium', 'high'}
        
        for typename, profile in MICROSCOPY_PROFILES.items():
            mag_levels = set(profile['magnification_feel'].keys())
            assert mag_levels == expected_levels, \
                f"{typename} magnification levels: expected {expected_levels}, got {mag_levels}"
    
    def test_color_palettes(self):
        """Test that all color palette modes are defined."""
        expected_palettes = {'scientific', 'artistic', 'monochrome'}
        
        for typename, profile in MICROSCOPY_PROFILES.items():
            palettes = set(profile['color_palette'].keys())
            assert palettes == expected_palettes, \
                f"{typename} color palettes: expected {expected_palettes}, got {palettes}"
    
    def test_vocabulary_items(self):
        """Test that vocabulary lists are non-empty."""
        for typename, profile in MICROSCOPY_PROFILES.items():
            assert profile['structure'], f"{typename}: structure is empty"
            assert profile['material'], f"{typename}: material is empty"
            assert profile['color'], f"{typename}: color is empty"
            assert profile['texture'], f"{typename}: texture is empty"


class TestEnhancementTools:
    """Test the MCP tools."""
    
    def test_list_types_returns_json(self):
        """Test that list_microscopy_types returns valid JSON."""
        import json
        result = list_microscopy_types()
        data = json.loads(result)
        assert len(data) == 7
        assert 'fluorescence' in data
    
    def test_get_profile_returns_json(self):
        """Test that get_microscopy_profile returns complete profile."""
        import json
        result = get_microscopy_profile('fluorescence')
        data = json.loads(result)
        assert data['display_name'] == 'Fluorescence'
        assert 'structure' in data
        assert 'magnification_feel' in data
    
    def test_invalid_type_error_handling(self):
        """Test that invalid type returns error message."""
        result = enhance_prompt_with_microscopy(
            'test prompt',
            'invalid_type'
        )
        assert 'Error' in result or 'Unknown' in result
    
    def test_suggest_types(self):
        """Test suggestion tool."""
        import json
        result = suggest_microscopy_type('glowing and luminous')
        data = json.loads(result)
        assert len(data) > 0
        # First suggestion should be fluorescence for glowing/luminous
        assert data[0]['type'] == 'fluorescence'


class TestPromptEnhancement:
    """Test prompt enhancement functionality."""
    
    def test_basic_enhancement(self):
        """Test basic prompt enhancement."""
        prompt = enhance_prompt_with_microscopy(
            'a butterfly wing',
            'fluorescence'
        )
        assert 'butterfly' in prompt.lower()
        assert 'fluorescence' in prompt.lower() or 'microscopy' in prompt.lower()
        assert 60 <= len(prompt.split()) <= 80
    
    def test_strength_parameter(self):
        """Test that strength parameter affects vocabulary density."""
        prompt_subtle = enhance_prompt_with_microscopy(
            'texture',
            'electron',
            aesthetic_strength='subtle'
        )
        prompt_strong = enhance_prompt_with_microscopy(
            'texture',
            'electron',
            aesthetic_strength='strong'
        )
        # Strong should have more characteristics
        assert len(prompt_strong.split()) >= len(prompt_subtle.split())
    
    def test_magnification_parameter(self):
        """Test that magnification affects language."""
        prompt_low = enhance_prompt_with_microscopy(
            'surface',
            'electron',
            magnification='low'
        )
        prompt_high = enhance_prompt_with_microscopy(
            'surface',
            'electron',
            magnification='high'
        )
        # Both should be valid prompts
        assert len(prompt_low.split()) > 5
        assert len(prompt_high.split()) > 5
    
    def test_color_palette_parameter(self):
        """Test that color palette affects vocabulary selection."""
        prompt_sci = enhance_prompt_with_microscopy(
            'test',
            'fluorescence',
            color_palette='scientific'
        )
        prompt_art = enhance_prompt_with_microscopy(
            'test',
            'fluorescence',
            color_palette='artistic'
        )
        # Both should be valid, likely with different color vocabulary
        assert len(prompt_sci.split()) > 5
        assert len(prompt_art.split()) > 5
    
    def test_word_count_target(self):
        """Test that enhanced prompts hit 60-80 word target."""
        for _ in range(5):
            prompt = enhance_prompt_with_microscopy(
                'a random object in nature',
                'fluorescence'
            )
            word_count = len(prompt.split())
            assert 60 <= word_count <= 80, \
                f"Word count {word_count} outside 60-80 range"


class TestAllMicroscopyTypes:
    """Test enhancement with all 7 types."""
    
    @pytest.mark.parametrize("mtype", [
        'fluorescence', 'electron', 'phase_contrast', 'confocal',
        'brightfield', 'darkfield', 'multiphoton'
    ])
    def test_all_types_work(self, mtype):
        """Test that all microscopy types produce valid output."""
        prompt = enhance_prompt_with_microscopy(
            'test subject',
            mtype
        )
        assert len(prompt) > 50
        assert 'highly detailed' in prompt.lower()
        assert 60 <= len(prompt.split()) <= 80


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
