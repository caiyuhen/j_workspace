from rest_framework import serializers
from .models import Trial, Site, InvestigationalProduct
from users.serializers import UserSerializer

class SiteSerializer(serializers.ModelSerializer):
    principal_investigator_details = UserSerializer(source='principal_investigator', read_only=True)
    assigned_cra_details = UserSerializer(source='assigned_cra', read_only=True)

    class Meta:
        model = Site
        fields = '__all__'

class TrialSerializer(serializers.ModelSerializer):
    sites = SiteSerializer(many=True, read_only=True)
    project_manager_details = UserSerializer(source='project_manager', read_only=True)

    class Meta:
        model = Trial
        fields = '__all__'
        read_only_fields = ['project_manager']

    def validate(self, data):
        # OQ-11: IRB - Trial status cannot be ACTIVE without IRB approval date
        if data.get('status') == 'ACTIVE':
            irb_date = data.get('irb_approval_date')
            # Check existing instance if updating
            if not irb_date and self.instance:
                 irb_date = self.instance.irb_approval_date
            
            if not irb_date:
                raise serializers.ValidationError({"status": "Cannot set status to ACTIVE without IRB Approval Date."})
        return data

class InvestigationalProductSerializer(serializers.ModelSerializer):
    trial_details = TrialSerializer(source='trial', read_only=True)

    class Meta:
        model = InvestigationalProduct
        fields = '__all__'
