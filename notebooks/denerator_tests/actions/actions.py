# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from typing import Text, Dict, Any, List
import json

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction
from rasa_sdk.events import SlotSet, UserUtteranceReverted, ConversationPaused

import config

logger = logging.getLogger(__name__)

class SubscribeNewsletterForm(FormAction):
    """Asks for the user's email, call the newsletter API and sign up user"""

    def name(self):
        return "subscribe_newsletter_form"

    @staticmethod
    def required_slots(tracker):
        return ["email"]

    def slot_mappings(self):
        return {
            "email": [
                self.from_entity(entity="email"),
                self.from_text(intent="enter_data"),
            ]
        }

    def validate_email(self, value, dispatcher, tracker, domain):
        """Check to see if an email entity was actually picked up by duckling."""

        if any(tracker.get_latest_entity_values("email")):
            # entity was picked up, validate slot
            return {"email": value}
        else:
            # no entity was picked up, we want to ask again
            dispatcher.utter_template("utter_no_email", tracker)
            return {"email": None}

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Once we have an email, attempt to add it to the database"""

        email = tracker.get_slot("email")
        client = MailChimpAPI(config.mailchimp_api_key)
        # if the email is already subscribed, this returns False
        added_to_list = client.subscribe_user(config.mailchimp_list, email)

        # utter submit template
        if added_to_list:
            dispatcher.utter_template("utter_confirmationemail", tracker)
        else:
            dispatcher.utter_template("utter_already_subscribed", tracker)
        return []


class SalesForm(FormAction):
    """Collects sales information and adds it to the spreadsheet"""

    def name(self):
        return "sales_form"

    @staticmethod
    def required_slots(tracker):
        return [
            "job_function",
            "use_case",
            "budget",
            "person_name",
            "company",
            "business_email",
        ]

    def slot_mappings(self):
        # type: () -> Dict[Text: Union[Dict, List[Dict]]]
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""

        return {
            "job_function": [
                self.from_entity(entity="job_function"),
                self.from_text(intent="enter_data"),
            ],
            "use_case": self.from_text(intent="enter_data"),
            "budget": [
                self.from_entity(entity="amount-of-money"),
                self.from_entity(entity="number"),
                self.from_text(intent="enter_data"),
            ],
            "person_name": [
                self.from_entity(entity="name"),
                self.from_text(intent="enter_data"),
            ],
            "company": [
                self.from_entity(entity="company"),
                self.from_text(intent="enter_data"),
            ],
            "business_email": [
                self.from_entity(entity="email"),
                self.from_text(intent="enter_data"),
            ],
        }

    def validate_business_email(self, value, dispatcher, tracker, domain):
        """Check to see if an email entity was actually picked up by duckling."""

        if any(tracker.get_latest_entity_values("email")):
            # entity was picked up, validate slot
            return {"business_email": value}
        else:
            # no entity was picked up, we want to ask again
            dispatcher.utter_template("utter_no_email", tracker)
            return {"business_email": None}

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Once we have all the information, attempt to add it to the
        Google Drive database"""

        import datetime

        budget = tracker.get_slot("budget")
        company = tracker.get_slot("company")
        email = tracker.get_slot("business_email")
        job_function = tracker.get_slot("job_function")
        person_name = tracker.get_slot("person_name")
        use_case = tracker.get_slot("use_case")
        date = datetime.datetime.now().strftime("%d/%m/%Y")

        sales_info = [company, use_case, budget, date, person_name, job_function, email]

        gdrive = GDriveService()
        try:
            gdrive.store_data(sales_info)
            dispatcher.utter_template("utter_confirm_salesrequest", tracker)
            return []
        except Exception as e:
            logger.error(
                "Failed to write data to gdocs. Error: {}" "".format(e.message),
                exc_info=True,
            )
            dispatcher.utter_template("utter_salesrequest_failed", tracker)
            return []


class ActionExplainSalesForm(Action):
    """Returns the explanation for the sales form questions"""

    def name(self):
        return "action_explain_sales_form"

    def run(self, dispatcher, tracker, domain):
        requested_slot = tracker.get_slot("requested_slot")

        if requested_slot not in SalesForm.required_slots(tracker):
            dispatcher.utter_message(
                "Sorry, I didn't get that. Please rephrase or answer the question "
                "above."
            )
            return []

        dispatcher.utter_template("utter_explain_" + requested_slot, tracker)
        return []


class ActionChitchat(Action):
    """Returns the chitchat utterance dependent on the intent"""

    def name(self):
        return "action_chitchat"

    def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message["intent"].get("name")

        # retrieve the correct chitchat utterance dependent on the intent
        if intent in [
            "ask_builder",
            "ask_weather",
            "ask_howdoing",
            "ask_whatspossible",
            "ask_whatisrasa",
            "ask_isbot",
            "ask_howold",
            "ask_languagesbot",
            "ask_restaurant",
            "ask_time",
            "ask_wherefrom",
            "ask_whoami",
            "handleinsult",
            "nicetomeeyou",
            "telljoke",
            "ask_whatismyname",
            "ask_howbuilt",
            "ask_whoisit",
        ]:
            dispatcher.utter_template("utter_" + intent, tracker)
        return []


class ActionFaqs(Action):
    """Returns the chitchat utterance dependent on the intent"""

    def name(self):
        return "action_faqs"

    def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message["intent"].get("name")

        # retrieve the correct chitchat utterance dependent on the intent
        if intent in [
            "ask_faq_platform",
            "ask_faq_languages",
            "ask_faq_tutorialcore",
            "ask_faq_tutorialnlu",
            "ask_faq_opensource",
            "ask_faq_voice",
            "ask_faq_slots",
            "ask_faq_channels",
            "ask_faq_differencecorenlu",
            "ask_faq_python_version",
            "ask_faq_community_size",
            "ask_faq_what_is_forum",
            "ask_faq_tutorials",
        ]:
            dispatcher.utter_template("utter_" + intent, tracker)
        return []


class ActionPause(Action):
    """Pause the conversation"""

    def name(self):
        return "action_pause"

    def run(self, dispatcher, tracker, domain):
        return [ConversationPaused()]


class ActionStoreUnknownProduct(Action):
    """Stores unknown tools people are migrating from in a slot"""

    def name(self):
        return "action_store_unknown_product"

    def run(self, dispatcher, tracker, domain):
        # if we dont know the product the user is migrating from,
        # store his last message in a slot.
        return [SlotSet("unknown_product", tracker.latest_message.get("text"))]


class ActionStoreUnknownNluPart(Action):
    """Stores unknown parts of nlu which the user requests information on
       in slot.
    """

    def name(self):
        return "action_store_unknown_nlu_part"

    def run(self, dispatcher, tracker, domain):
        # if we dont know the part of nlu the user wants information on,
        # store his last message in a slot.
        return [SlotSet("unknown_nlu_part", tracker.latest_message.get("text"))]


class ActionStoreBotLanguage(Action):
    """Takes the bot language and checks what pipelines can be used"""

    def name(self):
        return "action_store_bot_language"

    def run(self, dispatcher, tracker, domain):
        spacy_languages = [
            "english",
            "french",
            "german",
            "spanish",
            "portuguese",
            "french",
            "italian",
            "dutch",
        ]
        language = tracker.get_slot("language")
        if not language:
            return [
                SlotSet("language", "that language"),
                SlotSet("can_use_spacy", False),
            ]

        if language in spacy_languages:
            return [SlotSet("can_use_spacy", True)]
        else:
            return [SlotSet("can_use_spacy", False)]


class ActionStoreEntityExtractor(Action):
    """Takes the entity which the user wants to extract and checks
        what pipelines can be used.
    """

    def name(self):
        return "action_store_entity_extractor"

    def run(self, dispatcher, tracker, domain):
        spacy_entities = ["place", "date", "name", "organisation"]
        duckling = [
            "money",
            "duration",
            "distance",
            "ordinals",
            "time",
            "amount-of-money",
            "numbers",
        ]

        entity_to_extract = next(tracker.get_latest_entity_values("entity"), None)

        extractor = "CRFEntityExtractor"
        if entity_to_extract in spacy_entities:
            extractor = "SpacyEntityExtractor"
        elif entity_to_extract in duckling:
            extractor = "DucklingHTTPExtractor"

        return [SlotSet("entity_extractor", extractor)]


class ActionSetOnboarding(Action):
    """Sets the slot 'onboarding' to true/false dependent on whether the user
    has built a bot with rasa before"""

    def name(self):
        return "action_set_onboarding"

    def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message["intent"].get("name")
        user_type = next(tracker.get_latest_entity_values("user_type"), None)
        is_new_user = intent == "how_to_get_started" and user_type == "new"
        if intent == "affirm" or is_new_user:
            return [SlotSet("onboarding", True)]
        elif intent == "deny":
            return [SlotSet("onboarding", False)]
        return []


class SuggestionForm(FormAction):
    """Accept free text input from the user for suggestions"""

    def name(self):
        return "suggestion_form"

    @staticmethod
    def required_slots(tracker):
        return ["suggestion"]

    def slot_mappings(self):
        return {"suggestion": self.from_text()}

    def submit(self, dispatcher, tracker, domain):
        dispatcher.utter_template("utter_thank_suggestion", tracker)
        return []


class ActionStackInstallationCommand(Action):
    """Utters the installation command for rasa depending whether
       they are using `pip` or `conda`
    """

    def name(self):
        return "action_select_installation_command"

    def run(self, dispatcher, tracker, domain):
        package_manager = tracker.get_slot("package_manager")

        if package_manager == "conda":
            dispatcher.utter_template("utter_installation_with_conda", tracker)
        else:
            dispatcher.utter_template("utter_installation_with_pip", tracker)

        return []


class ActionStoreProblemDescription(Action):
    """Stores the problem description in a slot."""

    def name(self):
        return "action_store_problem_description"

    def run(self, dispatcher, tracker, domain):
        problem = tracker.latest_message.get("text")

        return [SlotSet("problem_description", problem)]


class ActionGreetUser(Action):
    """Greets the user with/without privacy policy"""

    def name(self):
        return "action_greet_user"

    def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message["intent"].get("name")
        shown_privacy = tracker.get_slot("shown_privacy")
        name_entity = next(tracker.get_latest_entity_values("name"), None)
        if intent == "greet":
            if shown_privacy and name_entity and name_entity.lower() != "sara":
                dispatcher.utter_template("utter_greet_name", tracker, name=name_entity)
                return []
            elif shown_privacy:
                dispatcher.utter_template("utter_greet_noname", tracker)
                return []
            else:
                dispatcher.utter_template("utter_greet", tracker)
                dispatcher.utter_template("utter_inform_privacypolicy", tracker)
                dispatcher.utter_template("utter_ask_goal", tracker)
                return [SlotSet("shown_privacy", True)]
        elif intent[:-1] == "get_started_step" and not shown_privacy:
            dispatcher.utter_template("utter_greet", tracker)
            dispatcher.utter_template("utter_inform_privacypolicy", tracker)
            dispatcher.utter_template("utter_" + intent, tracker)
            return [SlotSet("shown_privacy", True), SlotSet("step", intent[-1])]
        elif intent[:-1] == "get_started_step" and shown_privacy:
            dispatcher.utter_template("utter_" + intent, tracker)
            return [SlotSet("step", intent[-1])]
        return []


class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List["Event"]:

        # Fallback caused by TwoStageFallbackPolicy
        if (
            len(tracker.events) >= 4
            and tracker.events[-4].get("name") == "action_default_ask_affirmation"
        ):

            dispatcher.utter_template("utter_restart_with_button", tracker)

            return [SlotSet("feedback_value", "negative"), ConversationPaused()]

        # Fallback caused by Core
        else:
            dispatcher.utter_template("utter_default", tracker)
            return [UserUtteranceReverted()]


class ActionNextStep(Action):
    def name(self):
        return "action_next_step"

    def run(self, dispatcher, tracker, domain):
        step = int(tracker.get_slot("step")) + 1

        if step in [2, 3, 4]:
            dispatcher.utter_template("utter_continue_step{}".format(step), tracker)
        else:
            dispatcher.utter_template("utter_no_more_steps", tracker)

        return []

## API

from mailchimp3 import MailChimp
from mailchimp3.mailchimpclient import MailChimpError


class MailChimpAPI(object):
    """Class to connect to the MailChimp API"""

    def __init__(self, api_key):

        self.client = MailChimp(mc_api=api_key)

    def subscribe_user(self, list_id, email):
        # subscribe the user to the newsletter if they're not already
        # subscribed, with the status pending
        try:
            self.client.lists.members.create(
                list_id, data={"email_address": email, "status": "pending"}
            )
            return True

        # if the user is already subscribed, return False
        except MailChimpError:
            return False


from oauth2client.service_account import ServiceAccountCredentials
import gspread
import tempfile

class GDriveService(object):
    """Service to write to a spread sheet in google drive."""

    # Name of the spreadsheet
    SPREADSHEET_NAME = "Qualify Inbounds"

    # Sheet where the new address change entries should be stored in
    SHEET_NAME = "demobot"

    def __init__(self, gdrive_credentials_json=config.gdrive_credentials):
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        # authenticate the service with a json key
        with tempfile.NamedTemporaryFile(suffix="_credentials.json", mode="w") as f:
            f.write(gdrive_credentials_json)
            f.flush()
            self.credentials = ServiceAccountCredentials.from_json_keyfile_name(
                f.name, scopes=scopes
            )

    def request_sheet(self, sheet_name):
        # fetch a specific sheet
        logging.debug("Refreshing auth")
        try:
            return gspread.authorize(self.credentials).open(sheet_name)
        except Exception as e:
            logging.error(
                "Failed to create google spreadsheet connection. %s", e, exc_info=True
            )
            return None

    def store_data(self, data):
        """Adds a single new row to the sheet containing the user's
        information"""
        self.append_row(self.SPREADSHEET_NAME, data, self.SHEET_NAME)

    def append_row(self, sheet_name, row_values, worksheet_name):
        # add a row to the spreadsheet
        sheet = self.request_sheet(sheet_name)
        try:
            worksheet = sheet.worksheet(worksheet_name)
            if worksheet is not None:
                worksheet.append_row(row_values)
        except Exception as e:
            logging.error(
                "Failed to write row to gdocs. Sheet %s/%s. " + "Error: %s",
                sheet_name,
                worksheet_name,
                e,
                exc_info=True,
            )