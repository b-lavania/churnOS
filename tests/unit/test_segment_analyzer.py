"""Unit tests for segment performance analyzer functionality."""

import pytest
import pandas as pd
from analytics.conversion import analyze_segment_performance


class TestSegmentConversionRateCalculations:
    """Test segment conversion rate calculations."""

    def test_device_conversion_rates(self):
        """Test conversion rates are calculated correctly by device."""
        # 40 mobile sessions: 12 purchases (30% CVR)
        # 60 desktop sessions: 18 purchases (30% CVR)
        # Total: 30 purchases / 100 sessions = 30% overall CVR
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['mobile'] * 40 + ['desktop'] * 60,
            'source': ['organic'] * 100,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 100
        })
        # Assign purchases: 12 to mobile (indices 0-11), 18 to desktop (40-57)
        for idx in range(12):
            funnel_df.loc[idx, 'funnel_step'] = 'Purchase'
        for idx in range(40, 58):
            funnel_df.loc[idx, 'funnel_step'] = 'Purchase'
        
        result = analyze_segment_performance(funnel_df, 'device')
        
        # Overall CVR should be 30%
        assert result['overall_cvr'] == 30.0
        
        # Check segments DataFrame structure
        segments = result['segments']
        assert len(segments) == 2
        assert 'device' in segments.columns
        assert 'conversion_rate' in segments.columns
        
        # Verify conversion rates
        mobile_sessions = 40
        mobile_purchases = 12  # 30% of 40
        desktop_sessions = 60
        desktop_purchases = 18  # 30% of 60
        
        mobile_cvr = segments[segments['device'] == 'mobile']['conversion_rate'].values[0]
        desktop_cvr = segments[segments['device'] == 'desktop']['conversion_rate'].values[0]
        
        assert mobile_cvr == 30.0
        assert desktop_cvr == 30.0

    def test_source_conversion_rates(self):
        """Test conversion rates are calculated correctly by traffic source."""
        # 40 organic: 12 purchases (30%)
        # 30 paid: 9 purchases (30%)
        # 30 direct: 9 purchases (30%)
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['desktop'] * 100,
            'source': ['organic'] * 40 + ['paid'] * 30 + ['direct'] * 30,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 100
        })
        # Assign purchases: 12 organic (0-11), 9 paid (40-48), 9 direct (70-78)
        for idx in range(12):
            funnel_df.loc[idx, 'funnel_step'] = 'Purchase'
        for idx in range(40, 49):
            funnel_df.loc[idx, 'funnel_step'] = 'Purchase'
        for idx in range(70, 79):
            funnel_df.loc[idx, 'funnel_step'] = 'Purchase'
        
        result = analyze_segment_performance(funnel_df, 'source')
        
        # Overall CVR should be 30%
        assert result['overall_cvr'] == 30.0
        
        segments = result['segments']
        assert len(segments) == 3
        
        # Verify organic has 30% CVR (12 purchases / 40 sessions)
        organic_cvr = segments[segments['source'] == 'organic']['conversion_rate'].values[0]
        assert organic_cvr == 30.0

    def test_region_conversion_rates(self):
        """Test conversion rates are calculated correctly by region."""
        # 50 US: 15 purchases (30%)
        # 50 EU: 15 purchases (30%)
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['desktop'] * 100,
            'source': ['organic'] * 100,
            'region': ['US'] * 50 + ['EU'] * 50,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 70 + ['Purchase'] * 30
        })
        # Assign purchases: 15 US (indices 28-42), 15 EU (70-84)
        purchase_indices = list(range(28, 43)) + list(range(70, 85))
        for idx in purchase_indices:
            funnel_df.loc[idx, 'funnel_step'] = 'Purchase'
        
        result = analyze_segment_performance(funnel_df, 'region')
        
        segments = result['segments']
        assert len(segments) == 2
        
        # US: 15 purchases / 50 sessions = 30%
        us_cvr = segments[segments['region'] == 'US']['conversion_rate'].values[0]
        assert us_cvr == 30.0

    def test_visitor_type_conversion_rates(self):
        """Test conversion rates are calculated correctly by visitor type."""
        # 60 new: 18 purchases (30%)
        # 40 returning: 12 purchases (30%)
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['desktop'] * 100,
            'source': ['organic'] * 100,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 60 + ['returning'] * 40,
            'funnel_step': ['Visit'] * 70 + ['Purchase'] * 30
        })
        # Assign purchases: 18 new (indices 28-45), 12 returning (70-81)
        purchase_indices = list(range(28, 46)) + list(range(70, 82))
        for idx in purchase_indices:
            funnel_df.loc[idx, 'funnel_step'] = 'Purchase'
        
        result = analyze_segment_performance(funnel_df, 'visitor_type')
        
        segments = result['segments']
        assert len(segments) == 2
        
        # New: 18 purchases / 60 sessions = 30%
        new_cvr = segments[segments['visitor_type'] == 'new']['conversion_rate'].values[0]
        assert new_cvr == 30.0


class TestUnderperformingSegmentDetection:
    """Test underperforming segment detection."""

    def test_underperforming_mobile_detected(self):
        """Test that underperforming mobile segment is detected."""
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['mobile'] * 50 + ['desktop'] * 50,
            'source': ['organic'] * 100,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 85 + ['Purchase'] * 15
        })
        
        # Desktop: 15 purchases / 50 sessions = 30% CVR
        # Mobile: 0 purchases / 50 sessions = 0% CVR
        # Overall: 15 purchases / 100 sessions = 15% CVR
        # Mobile is 100% below average (should be flagged)
        
        result = analyze_segment_performance(funnel_df, 'device')
        
        underperforming = result['underperforming_segments']
        assert len(underperforming) > 0
        
        mobile_underperforming = any(
            seg['segment'] == 'mobile' for seg in underperforming
        )
        assert mobile_underperforming

    def test_underperforming_threshold_20_percent(self):
        """Test that segments 20%+ below average are flagged."""
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['mobile'] * 50 + ['desktop'] * 50,
            'source': ['organic'] * 100,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 80 + ['Purchase'] * 20
        })
        
        # Desktop: 20 purchases / 50 sessions = 40% CVR
        # Mobile: 0 purchases / 50 sessions = 0% CVR
        # Overall: 20 purchases / 100 sessions = 20% CVR
        # Mobile is 100% below average (should be flagged)
        
        result = analyze_segment_performance(funnel_df, 'device')
        
        underperforming = result['underperforming_segments']
        assert len(underperforming) > 0
        
        # Check that mobile is flagged
        mobile_seg = next(
            (seg for seg in underperforming if seg['segment'] == 'mobile'),
            None
        )
        assert mobile_seg is not None
        assert mobile_seg['cvr'] == 0.0
        assert mobile_seg['deficit_pct'] == 100.0

    def test_traffic_source_30_percent_threshold(self):
        """Test that traffic sources use 30% threshold for underperformance."""
        # Organic: 50 sessions, 15 purchases (30% CVR)
        # Paid: 50 sessions, 0 purchases (0% CVR)
        # Overall: 15 purchases / 100 sessions = 15% CVR
        # Paid is 100% below average (should be flagged with 30% threshold)
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['desktop'] * 100,
            'source': ['organic'] * 50 + ['paid'] * 50,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 100
        })
        # Assign 15 purchases to organic (0-14)
        for idx in range(15):
            funnel_df.loc[idx, 'funnel_step'] = 'Purchase'
        
        # Organic: 15 purchases / 50 sessions = 30% CVR
        # Paid: 0 purchases / 50 sessions = 0% CVR
        # Overall: 15 purchases / 100 sessions = 15% CVR
        # Paid is 100% below average (should be flagged with 30% threshold)
        
        result = analyze_segment_performance(funnel_df, 'source')
        
        underperforming = result['underperforming_segments']
        assert len(underperforming) > 0
        
        paid_underperforming = any(
            seg['segment'] == 'paid' for seg in underperforming
        )
        assert paid_underperforming

    def test_no_underperforming_segments_when_all_equal(self):
        """Test that no segments are flagged when all have equal performance."""
        # 50 mobile: 15 purchases (30%)
        # 50 desktop: 15 purchases (30%)
        # Overall: 30% - all segments equal, none should be flagged
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['mobile'] * 50 + ['desktop'] * 50,
            'source': ['organic'] * 100,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 100
        })
        # Assign 15 purchases to mobile (0-14) and 15 to desktop (50-64)
        for idx in range(15):
            funnel_df.loc[idx, 'funnel_step'] = 'Purchase'
        for idx in range(50, 65):
            funnel_df.loc[idx, 'funnel_step'] = 'Purchase'
        
        result = analyze_segment_performance(funnel_df, 'device')
        
        underperforming = result['underperforming_segments']
        assert len(underperforming) == 0


class TestSegmentSorting:
    """Test segment sorting by performance."""

    def test_sorts_by_conversion_rate_descending(self):
        """Test that segments are sorted by conversion rate in descending order."""
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['mobile'] * 40 + ['tablet'] * 30 + ['desktop'] * 30,
            'source': ['organic'] * 100,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 70 + ['Purchase'] * 30
        })
        
        result = analyze_segment_performance(funnel_df, 'device')
        
        segments = result['segments']
        conversion_rates = segments['conversion_rate'].tolist()
        
        # Check descending order
        assert conversion_rates == sorted(conversion_rates, reverse=True)

    def test_sorting_with_different_conversion_rates(self):
        """Test sorting with clearly different conversion rates."""
        # Desktop: 40 sessions, 20 purchases (50% CVR)
        # Tablet: 40 sessions, 6 purchases (15% CVR)
        # Mobile: 40 sessions, 4 purchases (10% CVR)
        funnel_df = pd.DataFrame({
            'session_id': range(120),
            'device': ['mobile'] * 40 + ['tablet'] * 40 + ['desktop'] * 40,
            'source': ['organic'] * 120,
            'region': ['US'] * 120,
            'visitor_type': ['new'] * 120,
            'funnel_step': ['Visit'] * 90 + ['Purchase'] * 30
        })
        # Assign purchases: 4 mobile (indices 28-31), 6 tablet (70-75), 20 desktop (90-109)
        for idx in range(28, 32):
            funnel_df.loc[idx, 'funnel_step'] = 'Purchase'
        for idx in range(70, 76):
            funnel_df.loc[idx, 'funnel_step'] = 'Purchase'
        for idx in range(90, 110):
            funnel_df.loc[idx, 'funnel_step'] = 'Purchase'
        
        result = analyze_segment_performance(funnel_df, 'device')
        
        segments = result['segments']
        devices = segments['device'].tolist()
        
        # Desktop should be first (highest CVR)
        assert devices[0] == 'desktop'
        # Mobile should be last (lowest CVR)
        assert devices[-1] == 'mobile'


class TestDeviceRecommendations:
    """Test device-specific recommendations."""

    def test_mobile_optimization_recommendation(self):
        """Test mobile optimization recommendations when mobile is underperforming."""
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['mobile'] * 50 + ['desktop'] * 50,
            'source': ['organic'] * 100,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 85 + ['Purchase'] * 15
        })
        
        result = analyze_segment_performance(funnel_df, 'device')
        
        recommendations = result['recommendations']
        assert len(recommendations) > 0
        
        # Check for mobile optimization recommendation
        mobile_recommendations = [
            r for r in recommendations if 'MOBILE' in r.upper()
        ]
        assert len(mobile_recommendations) > 0

    def test_desktop_recommendations(self):
        """Test desktop recommendations are generated."""
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['mobile'] * 50 + ['desktop'] * 50,
            'source': ['organic'] * 100,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 70 + ['Purchase'] * 30
        })
        
        result = analyze_segment_performance(funnel_df, 'device')
        
        recommendations = result['recommendations']
        desktop_recommendations = [
            r for r in recommendations if 'DESKTOP' in r.upper()
        ]
        assert len(desktop_recommendations) > 0

    def test_tablet_recommendations_when_traffic_exceeds_10_percent(self):
        """Test tablet recommendations when tablet traffic exceeds 10%."""
        funnel_df = pd.DataFrame({
            'session_id': range(120),
            'device': ['mobile'] * 50 + ['tablet'] * 20 + ['desktop'] * 50,
            'source': ['organic'] * 120,
            'region': ['US'] * 120,
            'visitor_type': ['new'] * 120,
            'funnel_step': ['Visit'] * 84 + ['Purchase'] * 36
        })
        
        result = analyze_segment_performance(funnel_df, 'device')
        
        recommendations = result['recommendations']
        tablet_recommendations = [
            r for r in recommendations if 'TABLET' in r.upper()
        ]
        assert len(tablet_recommendations) > 0


class TestTrafficSourceRecommendations:
    """Test traffic source recommendations."""

    def test_organic_recommendations(self):
        """Test organic traffic recommendations."""
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['desktop'] * 100,
            'source': ['organic'] * 50 + ['paid'] * 50,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 70 + ['Purchase'] * 30
        })
        
        result = analyze_segment_performance(funnel_df, 'source')
        
        recommendations = result['recommendations']
        organic_recommendations = [
            r for r in recommendations if 'ORGANIC' in r.upper()
        ]
        assert len(organic_recommendations) > 0

    def test_paid_recommendations(self):
        """Test paid traffic recommendations."""
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['desktop'] * 100,
            'source': ['organic'] * 50 + ['paid'] * 50,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 70 + ['Purchase'] * 30
        })
        
        result = analyze_segment_performance(funnel_df, 'source')
        
        recommendations = result['recommendations']
        paid_recommendations = [
            r for r in recommendations if 'PAID' in r.upper()
        ]
        assert len(paid_recommendations) > 0

    def test_underperforming_source_recommendations(self):
        """Test recommendations for underperforming traffic sources."""
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['desktop'] * 100,
            'source': ['organic'] * 50 + ['paid'] * 50,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 85 + ['Purchase'] * 15
        })
        
        # Paid: 0% CVR, Organic: 30% CVR, Overall: 15% CVR
        # Paid is 100% below average (should trigger recommendations)
        
        result = analyze_segment_performance(funnel_df, 'source')
        
        recommendations = result['recommendations']
        paid_recommendations = [
            r for r in recommendations if 'PAID TRAFFIC' in r.upper()
        ]
        assert len(paid_recommendations) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe_raises_error(self):
        """Test that empty DataFrame raises ValueError."""
        funnel_df = pd.DataFrame(columns=[
            'session_id', 'device', 'source', 'region', 'visitor_type', 'funnel_step'
        ])
        
        with pytest.raises(ValueError, match="funnel_df cannot be empty"):
            analyze_segment_performance(funnel_df, 'device')

    def test_missing_required_column_raises_error(self):
        """Test that missing required column raises ValueError."""
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['desktop'] * 100,
            'source': ['organic'] * 100,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100
            # Missing funnel_step
        })
        
        with pytest.raises(ValueError, match="funnel_df missing required columns"):
            analyze_segment_performance(funnel_df, 'device')

    def test_invalid_segment_by_raises_error(self):
        """Test that invalid segment_by raises ValueError."""
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['desktop'] * 100,
            'source': ['organic'] * 100,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 100
        })
        
        with pytest.raises(ValueError, match="funnel_df missing required columns"):
            analyze_segment_performance(funnel_df, 'invalid_dimension')

    def test_single_session(self):
        """Test handling of single session."""
        funnel_df = pd.DataFrame({
            'session_id': [1],
            'device': ['desktop'],
            'source': ['organic'],
            'region': ['US'],
            'visitor_type': ['new'],
            'funnel_step': ['Purchase']
        })
        
        result = analyze_segment_performance(funnel_df, 'device')
        
        assert result['overall_cvr'] == 100.0
        assert len(result['segments']) == 1

    def test_no_purchases(self):
        """Test handling of no purchases."""
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['desktop'] * 100,
            'source': ['organic'] * 100,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 100
        })
        
        result = analyze_segment_performance(funnel_df, 'device')
        
        assert result['overall_cvr'] == 0.0
        assert len(result['underperforming_segments']) == 0


class TestReturnStructure:
    """Test return structure of analyze_segment_performance."""

    def test_return_dict_has_all_required_keys(self):
        """Test that return dict has all required keys."""
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['desktop'] * 100,
            'source': ['organic'] * 100,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 70 + ['Purchase'] * 30
        })
        
        result = analyze_segment_performance(funnel_df, 'device')
        
        assert 'segments' in result
        assert 'overall_cvr' in result
        assert 'underperforming_segments' in result
        assert 'recommendations' in result

    def test_segments_dataframe_structure(self):
        """Test that segments DataFrame has correct structure."""
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['desktop'] * 100,
            'source': ['organic'] * 100,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 70 + ['Purchase'] * 30
        })
        
        result = analyze_segment_performance(funnel_df, 'device')
        
        segments = result['segments']
        assert isinstance(segments, pd.DataFrame)
        assert 'device' in segments.columns
        assert 'total_sessions' in segments.columns
        assert 'purchases' in segments.columns
        assert 'conversion_rate' in segments.columns

    def test_underperforming_segments_structure(self):
        """Test that underperforming_segments has correct structure."""
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['mobile'] * 50 + ['desktop'] * 50,
            'source': ['organic'] * 100,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 85 + ['Purchase'] * 15
        })
        
        result = analyze_segment_performance(funnel_df, 'device')
        
        underperforming = result['underperforming_segments']
        assert isinstance(underperforming, list)
        
        if len(underperforming) > 0:
            seg = underperforming[0]
            assert 'segment' in seg
            assert 'cvr' in seg
            assert 'total_sessions' in seg
            assert 'purchases' in seg
            assert 'deficit_pct' in seg

    def test_recommendations_is_list_of_strings(self):
        """Test that recommendations is a list of strings."""
        funnel_df = pd.DataFrame({
            'session_id': range(100),
            'device': ['desktop'] * 100,
            'source': ['organic'] * 100,
            'region': ['US'] * 100,
            'visitor_type': ['new'] * 100,
            'funnel_step': ['Visit'] * 70 + ['Purchase'] * 30
        })
        
        result = analyze_segment_performance(funnel_df, 'device')
        
        recommendations = result['recommendations']
        assert isinstance(recommendations, list)
        assert all(isinstance(r, str) for r in recommendations)
