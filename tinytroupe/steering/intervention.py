from typing import Union, List
from tinytroupe.extraction import logger
from tinytroupe.utils import JsonSerializableRegistry
from tinytroupe.experimentation import Proposition
from tinytroupe.environment import TinyWorld
from tinytroupe.agent import TinyPerson
import tinytroupe.utils as utils


# TODO under development
class Intervention:

    def __init__(self, targets: Union[TinyPerson, TinyWorld, List[TinyPerson], List[TinyWorld]], 
                 first_n:int=None, last_n:int=5,
                 name: str = None):
        """
        Initialize the intervention.

        Args:
            target (Union[TinyPerson, TinyWorld, List[TinyPerson], List[TinyWorld]]): the target to intervene on
            first_n (int): the number of first interactions to consider in the context
            last_n (int): the number of last interactions (most recent) to consider in the context
            name (str): the name of the intervention
        """
        
        self.targets = targets
        
        # initialize the possible preconditions
        self.text_precondition = None
        self.precondition_func = None

        # effects
        self.effect_func = None

        # which events to pay attention to?
        self.first_n = first_n
        self.last_n = last_n

        # name
        if name is None:
            self.name = self.name = f"Intervention {utils.fresh_id()}"
        else:
            self.name = name
        
        # the most recent precondition proposition used to check the precondition
        self._last_text_precondition_proposition = None
        self._last_functional_precondition_check = None

    ################################################################################################
    # Intervention flow
    ################################################################################################     
    
    def __call__(self):
        """
        Execute the intervention.

        Returns:
            bool: whether the intervention effect was applied.
        """
        return self.execute()

    def execute(self):
        """
        Execute the intervention. It first checks the precondition, and if it is met, applies the effect.
        This is the simplest method to run the intervention.

        Returns:
            bool: whether the intervention effect was applied.
        """
        logger.debug(f"Executing intervention: {self}")
        if self.check_precondition():
            self.apply_effect()
            logger.debug(f"Precondition was true, intervention effect was applied.")
            return True
        
        logger.debug(f"Precondition was false, intervention effect was not applied.")
        return False

    def check_precondition(self):
        """
        Check if the precondition for the intervention is met.
        """
        self._last_text_precondition_proposition = Proposition(self.targets, self.text_precondition, first_n=self.first_n, last_n=self.last_n)
        
        if self.precondition_func is not None:
            self._last_functional_precondition_check = self.precondition_func(self.targets)
        else:
            self._last_functional_precondition_check = True # default to True if no functional precondition is set
        
        llm_precondition_check = self._last_text_precondition_proposition.check()

        return llm_precondition_check and self._last_functional_precondition_check

    def apply_effect(self):
        """
        Apply the intervention's effects. This won't check the precondition, 
        so it should be called after check_precondition.
        """
        self.effect_func(self.targets)
    

    ################################################################################################
    # Pre and post conditions
    ################################################################################################

    def set_textual_precondition(self, text):
        """
        Set a precondition as text, to be interpreted by a language model.

        Args:
            text (str): the text of the precondition
        """
        self.text_precondition = text
        return self # for chaining
    
    def set_functional_precondition(self, func):
        """
        Set a precondition as a function, to be evaluated by the code.

        Args:
            func (function): the function of the precondition. 
              Must have the a single argument, targets (either a TinyWorld or TinyPerson, or a list). Must return a boolean.
        """
        self.precondition_func = func
        return self # for chaining
    
    def set_effect(self, effect_func):
        """
        Set the effect of the intervention.

        Args:
            effect (str): the effect function of the intervention
        """
        self.effect_func = effect_func
        return self # for chaining
    
    ################################################################################################
    # Inspection
    ################################################################################################

    def precondition_justification(self):
        """
        Get the justification for the precondition.
        """
        justification = ""

        # text precondition justification
        if self._last_text_precondition_proposition is not None:
            justification += f"{self._last_text_precondition_proposition.justification} (confidence = {self._last_text_precondition_proposition.confidence})\n\n"
        
        # functional precondition justification
        elif self._last_functional_precondition_check == True:
            justification += f"Functional precondition was met.\n\n"
        
        else:
            justification += "Preconditions do not appear to be met.\n\n"
        
        return justification
        


