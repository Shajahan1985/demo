"""
Filter form for asset list filtering.

This form provides filtering options for the asset list view,
including operating system, asset tag, team, and assigned user filters.
"""

from django import forms
from assets.models import OperatingSystem, Team


class AssetFilterForm(forms.Form):
    """Form for filtering assets in the asset list view."""
    
    operating_system = forms.ChoiceField(
        label='Operating System',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    asset_tag = forms.CharField(
        label='Asset Tag (BIDC Number)',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by asset tag...'
        })
    )
    
    team = forms.ChoiceField(
        label='Team',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    assigned_to = forms.CharField(
        label='Assigned To',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by user name...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        """
        Initialize form and populate dropdown choices from database.
        """
        super().__init__(*args, **kwargs)
        
        # Populate operating system choices
        os_choices = [('', '-- All Operating Systems --')]
        os_choices.extend([
            (os.id, os.name) 
            for os in OperatingSystem.objects.all().order_by('name')
        ])
        self.fields['operating_system'].choices = os_choices
        
        # Populate team choices
        team_choices = [('', '-- All Teams --')]
        team_choices.extend([
            (team.id, team.name) 
            for team in Team.objects.all().order_by('name')
        ])
        self.fields['team'].choices = team_choices
