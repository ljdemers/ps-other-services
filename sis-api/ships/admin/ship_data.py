import logging

from django.contrib import admin
from django.contrib.admin.widgets import AdminDateWidget
from django.core.exceptions import ValidationError
from django.forms import CharField, DateTimeField, ModelForm
from django.forms.models import model_to_dict
from django.utils.safestring import mark_safe

from ships.models import ShipData, ShipDataManualChange, ShipImage
from ships.models.managers.ship_data import ShipDataManager

log = logging.getLogger(__name__)


class ShipImageInline(admin.TabularInline):
    model = ShipImage
    extra = 0


class ShipDataModelForm(ModelForm):

    reason_of_change = CharField(required=True)
    mmsi_effective_from = DateTimeField(required=False, widget=AdminDateWidget)

    class Meta:
        model = ShipData
        fields = (
            "imo_id",
            "mmsi",
            "ship_name",
            "flag_name",
            "port_of_registry",
            "registered_owner",
            "call_sign",
            "length_overall_loa",
            "year_of_build",
            "flag",
            "operator",
            "technical_manager",
            "group_beneficial_owner",
        )

    def clean(self):
        form_data = self.cleaned_data
        initial_data = self.initial
        if initial_data["mmsi"] != form_data["mmsi"]:
            if (
                "mmsi_effective_from" not in form_data
                or form_data["mmsi_effective_from"] is None
            ):
                raise ValidationError(
                    "If you provide new MMSI you also have to provide"
                    " effective from date"
                )


class ShipDataAdmin(admin.ModelAdmin):
    """
    Admin screen to view data imported from IHS/SeaWeb. The full data is listed
    in a table, and some extracted information is shown as separate field.
    """

    list_display = (
        "imo_id",
        "ship_name",
        "mmsi",
        "flag_name",
        "port_of_registry",
        "registered_owner",
    )

    form = ShipDataModelForm
    readonly_fields = ("imo_id", "updated", "formatted_data")
    list_filter = ("flag_name",)
    search_fields = ("ship_name", "imo_id", "mmsi")
    inlines = [ShipImageInline]

    def compare_changes_between_data(self, new_object, old_data):
        # Convert object to a dict
        new_data_dict = model_to_dict(new_object)
        # Get rid of data dict, it can't be changed so we don't need it in diff
        new_data_dict.pop("data", None)
        # Match the keys between dicts
        # (the new object is bigger, because it also has uneditable fields)
        reduced_new_data = {
            k: new_data_dict[k] for k in new_data_dict if k in old_data.initial
        }
        # Get diff between them
        dict_diff_new = {
            k: reduced_new_data[k]
            for k, _ in set(reduced_new_data.items()) - set(old_data.initial.items())
        }
        dict_diff_old = {
            k: old_data.initial[k]
            for k, _ in set(old_data.initial.items()) - set(reduced_new_data.items())
        }

        return [dict_diff_new, dict_diff_old]

    def save_model(self, request, obj, form, change):
        # This method shouldn't be able to stop saving the model, but we can use
        # it for adding a "who changed what" ability

        # If user changed only the flag, but not the name
        # let's change it automatically
        if obj.flag is not None:
            if obj.flag_name != obj.flag.name:
                obj.flag_name = obj.flag.name

        dict_diff_new, dict_diff_old = self.compare_changes_between_data(
            new_object=obj, old_data=form
        )
        if "mmsi" in dict_diff_new:
            # We also need to correct the MMSI history entries
            ShipDataManager.create_or_update_mmsi_history(
                ShipData.objects.get(imo_id=obj.imo_id),
                dict_diff_new["mmsi"],
                date_from=form.cleaned_data["mmsi_effective_from"],
                manual_change=True,
            )
        # Reflect the changes also in the data dictionary
        for key, new_value in dict_diff_new.items():
            obj.data[key] = new_value
        # Found some changes between dicts
        if len(dict_diff_new) != 0:
            data_change = ShipDataManualChange(
                user=request.user,
                changed_ship=obj,
                old_data=dict_diff_old,
                new_data=dict_diff_new,
                reason=form.data["reason_of_change"],
            )
            data_change.save()
            logging.debug(
                "User %s has changed ShipData object id %s",
                request.user.username,
                obj.id,
            )
        super(ShipDataAdmin, self).save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return ["imo_id", "formatted_data"]

    def formatted_data(self, instance=None):
        """Format the raw data as a HTML table."""
        data = instance.data
        result = [
            '<tr><th style="text-align:left">Attribute</th><th style="text-align:left">Value</tr>'
        ]

        for key in sorted(data):
            readable_key = key.title().replace("_", " ")
            value = data[key]
            result.append(f"<tr><td>{readable_key}</td><td>{value}</td></tr>")

        return mark_safe("<table>{}</table>".format("\n".join(result)))

    formatted_data.allow_tags = True
    formatted_data.short_description = "Data"


admin.site.register(ShipData, ShipDataAdmin)
