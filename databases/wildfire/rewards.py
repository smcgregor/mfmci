"""
A set of reward functions used to generate rewards.
"""
import math


def reward_factory(parameter_dictionary):
    """
    Create the reward function.
    :param parameter_dictionary: The parameters sent by MDPvis.
    :return:
    """
    restoration_index_dollars = 1.0
    ponderosa_price_per_bf = 1.0
    mixed_conifer_price_per_bf = 1.0
    lodgepole_price_per_bf = 1.0
    airshed_smoke_reward_per_day = -1000.0
    recreation_index_dollars = 1.0
    suppression_expense_scale = 1.0
    discount = 0.96

    keys = parameter_dictionary.keys()
    if "restoration index dollars" in keys:
        restoration_index_dollars = float(parameter_dictionary["restoration index dollars"])
    if "ponderosa price per bf" in keys:
        restoration_index_dollars = float(parameter_dictionary["ponderosa price per bf"])
    if "mixed conifer price per bf" in keys:
        restoration_index_dollars = float(parameter_dictionary["mixed conifer price per bf"])
    if "lodgepole price per bf" in keys:
        restoration_index_dollars = float(parameter_dictionary["lodgepole price per bf"])
    if "airshed smoke reward per day" in keys:
        restoration_index_dollars = float(parameter_dictionary["airshed smoke reward per day"])
    if "recreation index dollars" in keys:
        restoration_index_dollars = float(parameter_dictionary["recreation index dollars"])
    if "suppression expense dollars" in keys:
        restoration_index_dollars = float(parameter_dictionary["suppression expense dollars"])
    if "discount" in keys:
        discount = float(parameter_dictionary["discount"])

    def reward_function(data,
                        restoration_index_dollars = restoration_index_dollars,
                        ponderosa_price_per_bf = ponderosa_price_per_bf,
                        mixed_conifer_price_per_bf = mixed_conifer_price_per_bf,
                        lodgepole_price_per_bf = lodgepole_price_per_bf,
                        airshed_smoke_reward_per_day = airshed_smoke_reward_per_day,
                        recreation_index_dollars = recreation_index_dollars,
                        suppression_expense_scale = suppression_expense_scale,
                        discount = discount):
        """

        :param data: The transitions we are assessing reward on
        :param restoration_index_dollars:
        :param ponderosa_price_per_bf:
        :param mixed_conifer_price_per_bf:
        :param lodgepole_price_per_bf:
        :param airshed_smoke_reward_per_day:
        :param recreation_index_dollars:
        :param suppression_expense_scale:
        :return: float for the reward
        """


        """
        Calculate the rewards for the trajectories.

        Hypothesis:
          Suppression probability increases with
            increased harvest value
            decreased restoration index value
            increased airshed reward
            increased recreation index
            decreased suppression expense

        todo: set the parameters of the reward function from the visualization.
        :param data:
        :return:
        """

        ### Reward Parameters ###
        restoration_index_dollars = 1.0  # How much squared deviations from the target ponderosa succession classes costs
        ponderosa_price_per_bf = 1.0
        mixed_conifer_price_per_bf = 1.0
        lodgepole_price_per_bf = 1.0
        airshed_smoke_reward_per_day = -1000.0  # How much each day of the fire costs
        recreation_index_dollars = 1.0  # How much squared deviations from the target cost
        suppression_expense_scale = 1.0  # How much to scale the costs of suppression

        def suppression_expense_reward(time_step):
            """
            Scale the suppression expense as modeled in the database and return.
            """
            expense = float(time_step["fireSuppressionCost"])
            return expense * suppression_expense_scale

        def airshed_reward(time_step):
            days = int(time_step["endIndex"]) - int(time_step["startIndex"])
            return airshed_smoke_reward_per_day * days

        def recreation_index_reward(time_step):
            """
            Total the squared deviation from the target old growth forest then scale it with a dollar amount.
            It would make sense to compute the squared deviation for all the cover types, but it would need to
            be weighted by the percent of the landscape in that cover type.
            """
            recreation_index_targets = {
                "ponderosaSC5": 100 #,
                #"mixedConSC5": 100,
                #"lodgepoleSC3": 100
            }

            total = 0.0
            for k in recreation_index_targets:
                total += math.pow(recreation_index_targets[k] - time_step[k], 2)
            return -total * recreation_index_dollars

        def harvest_reward(time_step):
            """
            Compute the economic value of the harvest according to the prices per board foot for each of the timber types.
            """
            total = 0.0
            total += float(time_step["boardFeetHarvestPonderosa"]) * ponderosa_price_per_bf
            total += float(time_step["boardFeetHarvestMixedConifer"]) * mixed_conifer_price_per_bf
            total += float(time_step["boardFeetHarvestLodgepole"]) * lodgepole_price_per_bf
            return total

        def restoration_index_reward(time_step):
            """
            Compute the squared deviation from the targets for the succession classes.
            """
            restoration_index_targets = {
                "ponderosaSC1": 10,
                "ponderosaSC2": 5,
                "ponderosaSC3": 35,
                "ponderosaSC4": 45,
                "ponderosaSC5": 5#,
                #"mixedConSC1": 10, # We don't care about the RI of the non-pondersoa species
                #"mixedConSC2": 5,
                #"mixedConSC3": 30,
                #"mixedConSC4": 45,
                #"mixedConSC5": 10,
                #"lodgepoleSC1": 25,
                #"lodgepoleSC2": 55,
                #"lodgepoleSC3": 20
            }

            total = 0.0
            for k in restoration_index_targets:
                total += math.pow(restoration_index_targets[k] - time_step[k], 2)
            return total * restoration_index_dollars

        harvest_total = 0
        restoration_index_total = 0.0
        airshed_total = 0.0
        recreation_index_total = 0.0
        suppression_expense_total = 0.0
        for trajectory in data["trajectories"]:
            for idx, time_step in enumerate(trajectory):
                restoration_index_total += restoration_index_reward(time_step)
                harvest_total += harvest_reward(time_step)
                airshed_total += airshed_reward(time_step)
                recreation_index_total += recreation_index_reward(time_step)
                suppression_expense_total += suppression_expense_reward(time_step)
        total = (harvest_total + restoration_index_total +
                 airshed_total + recreation_index_total + suppression_expense_total) * math.pow(discount, idx)
        return total
    return reward_function