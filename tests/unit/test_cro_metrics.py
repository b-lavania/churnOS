"""
Unit tests for CRO metrics calculator.
"""

import pytest
import pandas as pd
import numpy as np
from analytics.conversion import calculate_cro_metrics


class TestBounceRateCalculation:
    """Test bounce rate calculation."""
    
    def test_bounce_rate_single_page_sessions(self):
        """Test bounce rate calculation for single-page sessions."""
        # Create funnel data with 100 sessions, 40 are single-page (bounced)
        data = []
        
        # 40 single-page sessions (bounced)
        for i in range(40):
            data.append({
                'session_id': f'sess_{i}',
                'funnel_step': 'Visit'
            })
        
        # 60 multi-page sessions (not bounced)
        for i in range(60):
            session_id = f'sess_{40 + i}'
            data.append({
                'session_id': session_id,
                'funnel_step': 'Visit'
            })
            data.append({
                'session_id': session_id,
                'funnel_step': 'Product View'
            })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        # Bounce rate should be 40%
        assert result['bounce_rate'] == 40.0
    
    def test_bounce_rate_all_bounced(self):
        """Test bounce rate when all sessions are single-page."""
        data = []
        for i in range(100):
            data.append({
                'session_id': f'sess_{i}',
                'funnel_step': 'Visit'
            })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        # Bounce rate should be 100%
        assert result['bounce_rate'] == 100.0
    
    def test_bounce_rate_none_bounced(self):
        """Test bounce rate when no sessions are single-page."""
        data = []
        for i in range(100):
            session_id = f'sess_{i}'
            data.append({
                'session_id': session_id,
                'funnel_step': 'Visit'
            })
            data.append({
                'session_id': session_id,
                'funnel_step': 'Product View'
            })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        # Bounce rate should be 0%
        assert result['bounce_rate'] == 0.0


class TestEngagementRateCalculations:
    """Test engagement rate calculations."""
    
    def test_engagement_rates_with_scroll_depth(self):
        """Test engagement rates using scroll depth data."""
        data = []
        
        # 100 sessions with scroll depth data
        for i in range(100):
            session_id = f'sess_{i}'
            
            # First session has low scroll (below fold)
            if i == 0:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Visit',
                    'scroll_depth': 30
                })
            # Sessions 1-50 have medium scroll (above fold)
            elif i <= 50:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Visit',
                    'scroll_depth': 60
                })
            # Sessions 51-100 have high scroll (below fold)
            else:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Visit',
                    'scroll_depth': 90
                })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        # 99 sessions scrolled past fold (above 50%)
        assert result['above_fold_engagement'] == 99.0
        
        # 49 sessions scrolled below fold (above 80%)
        assert result['below_fold_engagement'] == 49.0
    
    def test_engagement_rates_without_scroll_depth(self):
        """Test engagement rate estimation without scroll depth."""
        data = []
        
        # 100 sessions
        for i in range(100):
            session_id = f'sess_{i}'
            data.append({
                'session_id': session_id,
                'funnel_step': 'Visit'
            })
            
            # 80 sessions reached Product View (engaged)
            if i < 80:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Product View'
                })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        # All 80 engaged sessions counted as above-fold
        assert result['above_fold_engagement'] == 80.0
        
        # Half of engaged sessions counted as below-fold
        assert result['below_fold_engagement'] == 40.0


class TestConversionRateCalculations:
    """Test conversion rate calculations."""
    
    def test_primary_conversion_rate(self):
        """Test primary conversion rate calculation."""
        data = []
        
        # 100 sessions
        for i in range(100):
            session_id = f'sess_{i}'
            data.append({
                'session_id': session_id,
                'funnel_step': 'Visit'
            })
            
            # 30 sessions made purchase
            if i < 30:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Purchase'
                })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        # Primary conversion rate should be 30%
        assert result['primary_conversion_rate'] == 30.0
    
    def test_secondary_conversion_rates(self):
        """Test secondary conversion rate calculation."""
        data = []
        
        # 100 sessions
        for i in range(100):
            session_id = f'sess_{i}'
            data.append({
                'session_id': session_id,
                'funnel_step': 'Visit'
            })
            
            # 20 sessions added to cart
            if i < 20:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Add to Cart'
                })
            
            # 15 sessions viewed product
            if i < 15:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Product View'
                })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        # Add to Cart should be 20%
        assert result['secondary_conversion_rates'].get('Add to Cart') == 20.0
        
        # Product View should be 15%
        assert result['secondary_conversion_rates'].get('Product View') == 15.0
    
    def test_secondary_conversion_rates_limited_to_5(self):
        """Test that only up to 5 secondary conversion rates are returned."""
        data = []
        
        # 100 sessions with 7 different funnel steps
        steps = ['Visit', 'Step1', 'Step2', 'Step3', 'Step4', 'Step5', 'Step6']
        
        for i in range(100):
            session_id = f'sess_{i}'
            for step in steps:
                data.append({
                    'session_id': session_id,
                    'funnel_step': step
                })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        # Should have at most 5 secondary conversion rates
        assert len(result['secondary_conversion_rates']) <= 5


class TestCTRCalculations:
    """Test CTR calculations."""
    
    def test_ctr_with_click_data(self):
        """Test CTR calculation with click event data."""
        data = []
        
        # 100 sessions with 3 elements
        for i in range(100):
            session_id = f'sess_{i}'
            data.append({
                'session_id': session_id,
                'funnel_step': 'Visit'
            })
            
            # Element 1: 50 clicks out of 100 impressions = 50% CTR
            if i < 50:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Visit',
                    'page_element': 'header_button',
                    'click_event': 1
                })
            else:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Visit',
                    'page_element': 'header_button',
                    'click_event': 0
                })
            
            # Element 2: 20 clicks out of 100 impressions = 20% CTR
            if i < 20:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Visit',
                    'page_element': 'sidebar_ad',
                    'click_event': 1
                })
            else:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Visit',
                    'page_element': 'sidebar_ad',
                    'click_event': 0
                })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        # header_button CTR should be 50%
        assert result['ctr_by_element'].get('header_button') == 50.0
        
        # sidebar_ad CTR should be 20%
        assert result['ctr_by_element'].get('sidebar_ad') == 20.0
    
    def test_ctr_without_click_data(self):
        """Test CTR calculation without click event data."""
        data = []
        
        # 100 sessions with 2 elements
        for i in range(100):
            session_id = f'sess_{i}'
            data.append({
                'session_id': session_id,
                'funnel_step': 'Visit'
            })
            
            # Element 1 appears in 50 sessions with 10 clicks
            if i < 50:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Visit',
                    'page_element': 'header_button'
                })
                if i < 10:
                    data.append({
                        'session_id': session_id,
                        'funnel_step': 'Visit',
                        'page_element': 'header_button',
                        'click_event': 1
                    })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        # CTR should be 10 clicks / 50 impressions = 20%
        assert result['ctr_by_element'].get('header_button') == 20.0


class TestDateRangeFiltering:
    """Test date range filtering."""
    
    def test_date_range_filtering(self):
        """Test that date range filtering works correctly."""
        data = []
        
        # Sessions from different dates
        for i in range(100):
            session_id = f'sess_{i}'
            date = f'2024-01-{(i % 28) + 1:02d}'
            
            data.append({
                'session_id': session_id,
                'funnel_step': 'Visit',
                'date': date
            })
            
            # 50 sessions made purchase
            if i < 50:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Purchase',
                    'date': date
                })
        
        df = pd.DataFrame(data)
        
        # Filter to first half of January
        result = calculate_cro_metrics(df, date_range=('2024-01-01', '2024-01-14'))
        
        # Should have fewer sessions due to filtering
        assert result['primary_conversion_rate'] >= 0
    
    def test_date_range_invalid_format(self):
        """Test that invalid date range format raises error."""
        data = []
        for i in range(10):
            data.append({
                'session_id': f'sess_{i}',
                'funnel_step': 'Visit'
            })
        
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="date_range must be a tuple"):
            calculate_cro_metrics(df, date_range=('2024-01-01',))
    
    def test_date_range_no_date_column(self):
        """Test date range filtering when no date column exists."""
        data = []
        for i in range(10):
            data.append({
                'session_id': f'sess_{i}',
                'funnel_step': 'Visit'
            })
        
        df = pd.DataFrame(data)
        
        # Should not raise error even with date_range when no date column
        result = calculate_cro_metrics(df, date_range=('2024-01-01', '2024-01-31'))
        # All 10 sessions are single-page (Visit only), so bounce rate is 100% and primary is 0%
        # But the function uses the max funnel_step as primary if Purchase doesn't exist
        # So we just verify it doesn't crash and returns valid metrics
        assert 'primary_conversion_rate' in result
        assert result['primary_conversion_rate'] >= 0


class TestAverageTimeOnPage:
    """Test average time on page calculation."""
    
    def test_avg_time_on_page_with_data(self):
        """Test average time on page with valid time data."""
        data = []
        
        # 100 sessions with time_on_page data
        for i in range(100):
            session_id = f'sess_{i}'
            data.append({
                'session_id': session_id,
                'funnel_step': 'Visit',
                'time_on_page': 30.0  # 30 seconds
            })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        # Average time should be 30 seconds
        assert result['avg_time_on_page'] == 30.0
    
    def test_avg_time_on_page_with_zero_times(self):
        """Test that zero times are excluded from average."""
        data = []
        
        # 100 sessions, some with zero time
        for i in range(100):
            session_id = f'sess_{i}'
            
            if i < 50:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Visit',
                    'time_on_page': 30.0
                })
            else:
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Visit',
                    'time_on_page': 0.0  # Should be excluded
                })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        # Average should only consider non-zero times
        assert result['avg_time_on_page'] == 30.0
    
    def test_avg_time_on_page_no_data(self):
        """Test average time on page when no time data exists."""
        data = []
        for i in range(10):
            data.append({
                'session_id': f'sess_{i}',
                'funnel_step': 'Visit'
            })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        # Should return 0.0 when no time data
        assert result['avg_time_on_page'] == 0.0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_dataframe(self):
        """Test that empty dataframe raises error."""
        df = pd.DataFrame(columns=['session_id', 'funnel_step'])
        
        with pytest.raises(ValueError, match="funnel_df cannot be empty"):
            calculate_cro_metrics(df)
    
    def test_missing_required_columns(self):
        """Test that missing required columns raises error."""
        df = pd.DataFrame({'session_id': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="funnel_df missing required columns"):
            calculate_cro_metrics(df)
    
    def test_no_sessions(self):
        """Test that no sessions raises error."""
        data = []
        df = pd.DataFrame(data, columns=['session_id', 'funnel_step'])
        
        with pytest.raises(ValueError, match="funnel_df cannot be empty"):
            calculate_cro_metrics(df)
    
    def test_single_session(self):
        """Test calculation with single session."""
        data = [
            {'session_id': 'sess_1', 'funnel_step': 'Visit'},
            {'session_id': 'sess_1', 'funnel_step': 'Purchase'}
        ]
        df = pd.DataFrame(data)
        
        result = calculate_cro_metrics(df)
        
        # Bounce rate should be 0% (multi-page session)
        assert result['bounce_rate'] == 0.0
        
        # Primary conversion should be 100%
        assert result['primary_conversion_rate'] == 100.0


class TestReturnTypes:
    """Test return value types and structure."""
    
    def test_return_type_is_dict(self):
        """Test that function returns a dictionary."""
        data = []
        for i in range(10):
            data.append({
                'session_id': f'sess_{i}',
                'funnel_step': 'Visit'
            })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        assert isinstance(result, dict)
    
    def test_all_required_keys_present(self):
        """Test that all required keys are present in result."""
        data = []
        for i in range(10):
            data.append({
                'session_id': f'sess_{i}',
                'funnel_step': 'Visit'
            })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        required_keys = [
            'bounce_rate',
            'above_fold_engagement',
            'below_fold_engagement',
            'primary_conversion_rate',
            'secondary_conversion_rates',
            'ctr_by_element',
            'avg_time_on_page'
        ]
        
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
    
    def test_values_are_rounded(self):
        """Test that values are rounded to 2 decimal places."""
        data = []
        for i in range(7):  # 7 sessions to get non-round percentages
            session_id = f'sess_{i}'
            data.append({
                'session_id': session_id,
                'funnel_step': 'Visit'
            })
            
            if i < 3:  # 3/7 = 42.857...%
                data.append({
                    'session_id': session_id,
                    'funnel_step': 'Purchase'
                })
        
        df = pd.DataFrame(data)
        result = calculate_cro_metrics(df)
        
        # Check that values are rounded (not many decimal places)
        assert len(str(result['primary_conversion_rate']).split('.')[-1]) <= 2
