from __future__ import annotations
import logging
from typing import Any, Dict, List, Set, Optional
from civicrm_client import CiviCRMClient

_logger = logging.getLogger("civicrm-mcp.gdpr")

class GDPRFieldFilter:
    """
    DSGVO-konformer Filter für CiviCRM-Daten.
    
    Strategie: Whitelist-Ansatz - nur explizit erlaubte Felder werden durchgelassen.
    Personenbezogene Daten werden entfernt und durch anonymisierte Platzhalter ersetzt.
    """
    
    # Felder die IMMER durchgelassen werden können (keine personenbezogenen Daten)
    ALLOWED_FIELDS: Dict[str, Set[str]] = {
        "Contact": {
            # IDs und Metadaten
            'id', 'contact_id', 'contact_type', 'contact_sub_type', 'external_identifier',
            
            # Preferences (keine personenbezogenen Daten)
            'do_not_email', 'do_not_phone', 'do_not_mail', 'do_not_sms', 'do_not_trade',
            'is_opt_out', 'preferred_communication_method', 'preferred_language',
            
            # Status-Felder
            'is_deleted', 'is_deceased',
            
            # Referenzen zu anderen Entities (nur IDs)
            'prefix_id', 'suffix_id', 'gender_id', 'communication_style_id',
            'email_greeting_id', 'postal_greeting_id', 'addressee_id',
            'employer_id',  # Nur ID, nicht der Name!
            
            # Timestamps
            'created_date', 'modified_date',
            
            # Verlinkungen (IDs, keine sensitiven Daten)
            'primary_contact_id', 'master_id',
            
            # Aggregierte/abgeleitete Felder (keine direkten personenbezogenen Daten)
            'contact_is_deleted', 'user_unique_id',
            
            # Primärmarkierungen
            'address_primary.id', 'address_billing.id', 
            'email_primary.id', 'phone_primary.id', 'im_primary.id',
            
            # Gruppen und Tags (IDs)
            'groups', 'tags',
            
            # Source (meist unkritisch)
            'source',
            
            # Alter in Jahren (nicht Geburtsdatum!)
            'age_years',
        },
        
        'Address': {
            # IDs und Metadaten
            'id', 'contact_id', 'location_type_id',
            
            # Primärmarkierungen
            'is_primary', 'is_billing',
            
            # Aggregierte Geo-Daten (Bundesland, Land - nicht Straße/PLZ!) - doch Stadt, aber nicht Postleitzahl
            'county_id', 'state_province_id', 'country_id', "city",
            
            # Technische Felder
            'manual_geo_code', 'timezone', 'master_id',
        },
        
        'Email': {
            'id', 'contact_id', 'location_type_id',
            'is_primary', 'is_billing',
            'on_hold', 'is_bulkmail',
            'hold_date', 'reset_date',
            # email-Feld selbst ist NICHT erlaubt!
        },
        
        'Phone': {
            'id', 'contact_id', 'location_type_id',
            'is_primary', 'is_billing',
            'phone_type_id',
            # phone und phone_ext sind NICHT erlaubt!
        },
        
        'IM': {
            'id', 'contact_id', 'location_type_id',
            'is_primary',
            'provider_id',
            # name (der IM-Handle) ist NICHT erlaubt!
        },
        
        'Website': {
            'id', 'contact_id',
            'website_type_id',
            # url ist kontextabhängig - erstmal NICHT erlaubt
        },
        
        'Note': {
            'id', 'entity_id', 'entity_table',
            'contact_id',
            'modified_date', 'created_date',
            'privacy',
            # subject und note sind NICHT erlaubt (oft persönliche Infos)!
        },
        
        'Activity': {
            'id', 'source_contact_id', 'activity_type_id',
            'status_id', 'priority_id',
            'activity_date_time', 'duration',
            'is_test', 'is_deleted', 'is_current_revision',
            'created_date', 'modified_date',
            'campaign_id', 'engagement_level',
            # subject und details sind NICHT erlaubt (oft persönliche Infos)!
        },
        
        'Contribution': {
            'id', 'contact_id', 'financial_type_id',
            'contribution_page_id', 'payment_instrument_id',
            'receive_date', 'cancel_date', 'receipt_date', 'thankyou_date',
            'total_amount', 'fee_amount', 'net_amount', 'tax_amount',
            'currency', 'contribution_status_id',
            'is_test', 'is_pay_later',
            'campaign_id',
            'created_date', 'modified_date',
            # source, check_number könnten Namen enthalten - NICHT erlaubt
        },
        
        'Membership': {
            'id', 'contact_id', 'membership_type_id',
            'join_date', 'start_date', 'end_date',
            'status_id', 'is_override', 'is_test',
            'contribution_recur_id',
            'campaign_id',
            'created_date', 'modified_date',
            # source könnte Namen enthalten - NICHT erlaubt
        },
        
        'Participant': {
            'id', 'contact_id', 'event_id',
            'status_id', 'role_id',
            'register_date', 'created_date', 'modified_date',
            'fee_level', 'fee_amount', 'fee_currency',
            'discount_id', 'is_test', 'is_pay_later',
            'campaign_id',
        },
        
        'Event': {
            'id', 'title', 'event_type_id',
            'start_date', 'end_date',
            'is_public', 'is_online_registration', 'is_monetary',
            'max_participants', 'is_active', 'is_template',
            'created_date', 'modified_date',
            # summary, description könnten personenbezogene Daten enthalten - vorsichtig!
        },
        
        'Relationship': {
            'id', 'contact_id_a', 'contact_id_b',
            'relationship_type_id',
            'start_date', 'end_date',
            'is_active', 'is_permission_a_b', 'is_permission_b_a',
            'created_date', 'modified_date',
            # description könnte personenbezogene Daten enthalten - NICHT erlaubt
        },
        
        'Case': {
            'id', 'contact_id', 'case_type_id', 'status_id',
            'start_date', 'end_date',
            'is_deleted',
            'created_date', 'modified_date',
            # subject könnte personenbezogene Daten enthalten - NICHT erlaubt
        },
        
        'Group': {
            'id', 'name', 'title', 'description',
            'group_type', 'visibility',
            'is_active', 'is_hidden', 'is_reserved',
            'created_date', 'modified_date',
            # Groups selbst sind OK (keine personenbezogenen Daten)
        },
        
        'Tag': {
            'id', 'name', 'description',
            'is_selectable', 'is_reserved', 'is_tagset',
            'parent_id', 'created_date', 'modified_date',
            # Tags selbst sind OK (keine personenbezogenen Daten)
        },
    }
    
    # Felder die aggregiert/anonymisiert werden können
    AGGREGATE_FIELDS: Dict[str, Set[str]] = {
        'Contact': {
            'first_name', 'middle_name', 'last_name', 'display_name', 
            'sort_name', 'nick_name', 'legal_name',
            'organization_name', 'household_name',
            'birth_date', 'deceased_date',
            'image_URL',
        },
        'Address': {
            'street_address', 'street_number', 'street_name', 'street_unit',
            'supplemental_address_1', 'supplemental_address_2', 'supplemental_address_3',
            'city', 'postal_code', 'postal_code_suffix',
            'geo_code_1', 'geo_code_2',
            'name',
        },
        'Email': {
            'email',
        },
        'Phone': {
            'phone', 'phone_ext', 'phone_numeric',
        },
        'IM': {
            'name',  # IM-Handle
        },
        'Note': {
            'subject', 'note',
        },
        'Activity': {
            'subject', 'details', 'location',
        },
    }
    
    @classmethod
    def filter_response(cls, entity: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filtert eine CiviCRM API-Response und entfernt personenbezogene Daten.
        
        Args:
            entity: Der Entity-Name (z.B. "Contact", "Address")
            response: Die Original-Response vom CiviCRM API
            
        Returns:
            Gefilterte Response mit entfernten personenbezogenen Daten
        """
        if not isinstance(response, dict):
            return response
        
        # Response-Struktur beibehalten
        filtered = response.copy()
        
        # Values-Array filtern
        if 'values' in filtered and isinstance(filtered['values'], list):
            filtered['values'] = [
                cls._filter_record(entity, record) 
                for record in filtered['values']
            ]
        
        _logger.debug(f"Filtered {entity} response: {len(filtered.get('values', []))} records")
        return filtered

    @classmethod
    async def filter_searchdisplay_response(
        cls, savedSearch: Dict[str, Any], response: Dict[str, Any]
    ) -> Dict[str, Any]:
        filtered = response.copy()
        if "values" not in savedSearch:
            return cls.filter_response("SearchDisplay", response)
        values = savedSearch["values"]
        if not isinstance(values, list):
            return cls.filter_response("SearchDisplay", response)
        saved_search_value = values[0]
        if "api_entity" not in saved_search_value:
            return cls.filter_response("SearchDisplay", response)
        base_entity = saved_search_value["api_entity"]
        fields_to_entity_field: dict[str, tuple[str, str]] = {}

        # Handle explicit joins
        if "api_params" in saved_search_value:
            if "select" in saved_search_value["api_params"]:
                fields = saved_search_value["api_params"]["select"]
            else:
                fields = []
            if "join" in saved_search_value["api_params"]:
                for join in saved_search_value["api_params"]["join"]:
                    if isinstance(join, list):
                        entity_as_alias: str = join[0]
                        entity, alias = entity_as_alias.split(" AS ", 1)
                        for field in fields:
                            field: str
                            if alias in field:
                                fields_to_entity_field[field] = (
                                    entity,
                                    field.replace(alias + ".", "", 1),
                                )
                                fields.remove(field)
        else:
            fields = []
        for field in fields:
            fields_to_entity_field[field] = base_entity, field

        # Handle implicit joins
        fields_to_entity_field = {
            k: await cls._get_implicitly_joined_entity_and_field(entity, field)
            for k, (entity, field) in fields_to_entity_field.items()
        }

        if "values" in filtered and isinstance(filtered["values"], list):
            filtered["values"] = [
                {
                    "data": cls._filter_joined_record(
                        record["data"], fields_to_entity_field, base_entity
                    )
                }
                for record in filtered["values"]
                if "data" in record
            ]

        return filtered

    @classmethod
    async def _get_implicitly_joined_entity_and_field(
        cls, original_entity: str, field: str
    ) -> tuple[str, str]:
        # TODO: if performance is bad we can cache what the implicit joins are
        if "." not in field:
            return original_entity, field
        field_with_fk, fk_field = field.split(".", 1)
        async with CiviCRMClient() as cli:
            field_info = await cli.call(
                original_entity,
                "getFields",
                {"where": [["name", "=", field_with_fk]], "select": ["fk_entity"]},
            )
        if (
            "values" in field_info
            and isinstance(field_info["values"], list)
            and len(field_info["values"]) > 0
            and "fk_entity" in field_info["values"][0]
        ):
            return await cls._get_implicitly_joined_entity_and_field(
                field_info["values"][0]["fk_entity"], fk_field
            )
        return original_entity, field

    @classmethod
    def _filter_record(cls, entity: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filtert einen einzelnen Record und entfernt personenbezogene Felder.
        """
        if not isinstance(record, dict):
            return record
        
        allowed = cls.ALLOWED_FIELDS.get(entity, set())
        aggregate = cls.AGGREGATE_FIELDS.get(entity, set())
        
        filtered = {}
        removed_fields = []
        
        for key, value in record.items():
            # Immer ID durchlassen
            if cls._is_field_whitelisted(entity, key, allowed, aggregate):
                filtered[key] = value
            else:
                removed_fields.append(key)
        
        # Anonymisierte Ersatzfelder hinzufügen
        filtered = cls._add_anonymized_fields(entity, record, filtered)
        
        if removed_fields:
            _logger.debug(f"Removed {len(removed_fields)} fields from {entity}: {removed_fields[:5]}...")
        
        return filtered

    @classmethod
    def _filter_joined_record(
        cls,
        record: Dict[str, Any],
        fields_to_entity_field: Dict[str, tuple[str, str]],
        base_entity: str,
    ) -> Dict[str, Any]:
        if not isinstance(record, dict):
            return record

        filtered = {}
        removed_fields = []

        for key, value in record.items():
            entity, field = fields_to_entity_field[key]
            if cls._is_field_whitelisted(
                entity,
                field,
                cls.ALLOWED_FIELDS.get(entity, set()),
                cls.AGGREGATE_FIELDS.get(entity, set()),
            ):
                filtered[key] = value
            else:
                removed_fields.append(key)

        for entity in [entity for _, (entity, _) in fields_to_entity_field.items()]:
            _logger.debug(f"Added anonymized fields for entity {entity}")
            filtered = cls._add_anonymized_fields(
                entity,
                {
                    field: True
                    for _, (_entity, field) in fields_to_entity_field.items()
                    if _entity == entity
                },
                filtered,
            )

        if removed_fields:
            _logger.debug(
                f"Removed {len(removed_fields)} fields from {base_entity}: {removed_fields[:5]}...\n"
            )

        return filtered

    @classmethod
    def _is_field_whitelisted(
        cls, entity, key, allowed: Set[str] = set(), aggregate: Set[str] = set()
    ) -> bool:
        # Immer ID durchlassen
        if key == "id" or key.endswith("_id") or key.endswith(".id"):
            return True
        # Erlaubte Felder durchlassen
        elif key in allowed:
            return True
        # Aggregierbare Felder werden entfernt und geloggt
        elif key in aggregate:
            return False
        # Unbekannte Felder: Bei unbekannten Entities nur IDs durchlassen
        elif entity not in cls.ALLOWED_FIELDS:
            # Unbekannte Entity: sehr restriktiv, nur IDs
            if key.endswith("_id") or key.endswith(".id"):
                return True
            else:
                return False
        # Alles andere wird entfernt
        else:
            return False

    @classmethod
    def _add_anonymized_fields(
        cls, 
        entity: str, 
        original: Dict[str, Any], 
        filtered: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fügt anonymisierte Ersatzfelder hinzu (z.B. "Contact #123" statt Namen).
        """
        result = filtered.copy()

        if entity == 'Contact':
            # Anonymisierter Display-Name statt echtem Namen
            if 'id' in result:
                contact_type = result.get('contact_type', 'Contact')
                result['_display_name'] = f"{contact_type} #{result['id']}"
            
            # Altersgruppe statt Geburtsdatum
            if 'birth_date' in original and original['birth_date']:
                # Hier könnte man Altersgruppen berechnen (0-18, 19-30, etc.)
                result['_has_birth_date'] = True
            
            # Hinweis auf gelöschte Felder
            aggregate = cls.AGGREGATE_FIELDS.get(entity, set())
            removed = [k for k in original.keys() if k in aggregate]
            if removed:
                result['_filtered_fields'] = list(
                    set(result.get('_filtered_fields', []) + removed)
                )

        elif entity == 'Address':
            # Nur Region statt vollständiger Adresse
            if 'country_id' in result:
                result['_has_address'] = True
                result['_location_level'] = 'country'
            if 'state_province_id' in result:
                result['_location_level'] = 'state'
            
            aggregate = cls.AGGREGATE_FIELDS.get(entity, set())
            removed = [k for k in original.keys() if k in aggregate]
            if removed:
                result['_filtered_fields'] = list(
                    set(result.get('_filtered_fields', []) + removed)
                )

        elif entity == 'Email':
            if 'email' in original:
                result['_has_email'] = True
                result['_filtered_fields'] = list(
                    set(result.get('_filtered_fields', []) + ['email'])
                )

        elif entity == 'Phone':
            if 'phone' in original:
                result['_has_phone'] = True
                result['_filtered_fields'] = list(
                    set(result.get('_filtered_fields', []) + ['phone', 'phone_ext'])
                )

        elif entity == 'Activity':
            if 'subject' in original or 'details' in original:
                result['_has_content'] = True
                result['_filtered_fields'] = list(
                    set(
                        result.get('_filtered_fields', [])
                        + [
                            k
                            for k in ['subject', 'details', 'location']
                            if k in original
                        ]
                    )
                )

        elif entity == 'Note':
            if 'note' in original or 'subject' in original:
                result['_has_content'] = True
                result['_filtered_fields'] = list(
                    set(
                        result.get('_filtered_fields', [])
                        + [k for k in ['subject', 'note'] if k in original]
                    )
                )

        return result
    
    @classmethod
    def get_allowed_fields_for_entity(cls, entity: str) -> Set[str]:
        """
        Gibt die Liste der erlaubten Felder für eine Entity zurück.
        Nützlich für die Dokumentation oder Debugging.
        """
        return cls.ALLOWED_FIELDS.get(entity, set())
    
    @classmethod
    def is_field_allowed(cls, entity: str, field: str) -> bool:
        """
        Prüft ob ein bestimmtes Feld für eine Entity erlaubt ist.
        """
        # IDs sind immer erlaubt
        if field == 'id' or field.endswith('_id') or field.endswith('.id'):
            return True
        
        allowed = cls.ALLOWED_FIELDS.get(entity, set())
        return field in allowed
