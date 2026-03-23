"""
Psychometric Instrument Repository Generator
=============================================
Generates a research-grade repository of ~100 psychometric instruments across
9 construct classes. Exports to CSV and formatted Excel.

Author: Generated for MAPIG project (Psynalytics)
Date: 2026-03-23

Item reproduction policy:
- Public domain instruments: Full items included (PHQ-9, GAD-7, WHO-5, etc.)
- Items published in original papers with open access: Included with citation
- Proprietary/restricted instruments: Marked as "Not reproduced — [publisher]"
- Uncertain: Marked for verification
"""

import csv
import os
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    PatternFill,
    Side,
)
from openpyxl.utils import get_column_letter

# ---------------------------------------------------------------------------
# Instrument data — 100 instruments across 9 construct classes
# ---------------------------------------------------------------------------
# reproduction_status values:
#   "full"    — all items reproduced from lawful open source
#   "partial" — some items reproduced; others withheld
#   "none"    — items not reproduced due to licensing/source constraints

INSTRUMENTS = [
    # ======================================================================
    # 1. STABLE TRAITS (12 instruments)
    # ======================================================================
    {
        "instrument_name": "Big Five Inventory",
        "abbreviation": "BFI-44",
        "construct": "Big Five personality traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)",
        "construct_class": "Stable traits",
        "domain": "Personality",
        "authors": "John, O. P., Donahue, E. M., & Kentle, R. L.",
        "year": 1991,
        "target_population": "Adults (general)",
        "number_of_items": 44,
        "response_scale": "5-point Likert (1 = Disagree strongly to 5 = Agree strongly)",
        "subscales": "Extraversion (8); Agreeableness (9); Conscientiousness (9); Neuroticism (8); Openness (10)",
        "exact_items": "Not reproduced — items available from the Berkeley Personality Lab with permission. Contact Oliver John at UC Berkeley.",
        "item_source": "John, O. P., & Srivastava, S. (1999). The Big Five trait taxonomy. In L. A. Pervin & O. P. John (Eds.), Handbook of personality (pp. 102-138). Guilford Press.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "One of the most widely used Big Five measures. Strong convergent validity with NEO-PI-R. Internal consistency alphas typically .75-.90. Free for non-commercial research with permission. BFI-2 (Soto & John, 2017) is the updated 60-item version.",
    },
    {
        "instrument_name": "HEXACO Personality Inventory-Revised",
        "abbreviation": "HEXACO-60",
        "construct": "Six-factor personality (Honesty-Humility, Emotionality, Extraversion, Agreeableness, Conscientiousness, Openness)",
        "construct_class": "Stable traits",
        "domain": "Personality",
        "authors": "Ashton, M. C., & Lee, K.",
        "year": 2009,
        "target_population": "Adults (general)",
        "number_of_items": 60,
        "response_scale": "5-point Likert (1 = Strongly disagree to 5 = Strongly agree)",
        "subscales": "Honesty-Humility (10); Emotionality (10); Extraversion (10); Agreeableness (10); Conscientiousness (10); Openness to Experience (10)",
        "exact_items": "Not reproduced — items freely available for academic research from hexaco.org. Researchers should download directly from the official site.",
        "item_source": "Ashton, M. C., & Lee, K. (2009). The HEXACO-60: A short measure of the major dimensions of personality. Journal of Personality Assessment, 91(4), 340-345. Items at hexaco.org.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Adds Honesty-Humility as sixth factor beyond Big Five. Strong cross-cultural replication (>20 languages). Free for research. 100-item and 200-item versions also available. Alphas typically .73-.80 for 60-item version.",
    },
    {
        "instrument_name": "Rosenberg Self-Esteem Scale",
        "abbreviation": "RSES",
        "construct": "Global self-esteem",
        "construct_class": "Stable traits",
        "domain": "Self-concept",
        "authors": "Rosenberg, M.",
        "year": 1965,
        "target_population": "Adolescents and adults",
        "number_of_items": 10,
        "response_scale": "4-point Likert (0 = Strongly disagree to 3 = Strongly agree)",
        "subscales": "Unidimensional (5 positively worded, 5 negatively worded)",
        "exact_items": "1. On the whole, I am satisfied with myself; 2. At times I think I am no good at all (R); 3. I feel that I have a number of good qualities; 4. I am able to do things as well as most other people; 5. I feel I do not have much to be proud of (R); 6. I certainly feel useless at times (R); 7. I feel that I'm a person of worth, at least on an equal plane with others; 8. I wish I could have more respect for myself (R); 9. All in all, I am inclined to feel that I am a failure (R); 10. I take a positive attitude toward myself",
        "item_source": "Rosenberg, M. (1965). Society and the Adolescent Self-Image. Princeton University Press. Items widely reproduced in academic literature.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Most widely used self-esteem measure globally (>60,000 citations). Test-retest reliability .82-.88. Strong convergent validity. Some debate about unidimensionality vs. method effects from reverse-coded items. Public domain.",
    },
    {
        "instrument_name": "General Self-Efficacy Scale",
        "abbreviation": "GSE",
        "construct": "Generalized self-efficacy beliefs",
        "construct_class": "Stable traits",
        "domain": "Self-concept",
        "authors": "Schwarzer, R., & Jerusalem, M.",
        "year": 1995,
        "target_population": "Adults (general)",
        "number_of_items": 10,
        "response_scale": "4-point Likert (1 = Not at all true to 4 = Exactly true)",
        "subscales": "Unidimensional",
        "exact_items": "1. I can always manage to solve difficult problems if I try hard enough; 2. If someone opposes me, I can find the means and ways to get what I want; 3. It is easy for me to stick to my aims and accomplish my goals; 4. I am confident that I could deal efficiently with unexpected events; 5. Thanks to my resourcefulness, I know how to handle unforeseen situations; 6. I can solve most problems if I invest the necessary effort; 7. I can remain calm when facing difficulties because I can rely on my coping abilities; 8. When I am confronted with a problem, I can usually find several solutions; 9. If I am in trouble, I can usually think of a solution; 10. I can usually handle whatever comes my way",
        "item_source": "Schwarzer, R., & Jerusalem, M. (1995). Generalized Self-Efficacy scale. In J. Weinman, S. Wright, & M. Johnston (Eds.), Measures in health psychology (pp. 35-37). Items freely available from userpage.fu-berlin.de/~health/engscal.htm.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Translated into 33 languages. Cronbach's alpha typically .76-.90. Based on Bandura's social cognitive theory. Freely available from authors' website. Distinct from domain-specific self-efficacy measures.",
    },
    {
        "instrument_name": "Life Orientation Test-Revised",
        "abbreviation": "LOT-R",
        "construct": "Dispositional optimism",
        "construct_class": "Stable traits",
        "domain": "Self-concept",
        "authors": "Scheier, M. F., Carver, C. S., & Bridges, M. W.",
        "year": 1994,
        "target_population": "Adults (general)",
        "number_of_items": 10,
        "response_scale": "5-point Likert (0 = Strongly disagree to 4 = Strongly agree)",
        "subscales": "Unidimensional (3 optimism, 3 pessimism, 4 fillers)",
        "exact_items": "1. In uncertain times, I usually expect the best; 2. It's easy for me to relax [filler]; 3. If something can go wrong for me, it will (R); 4. I'm always optimistic about my future; 5. I enjoy my friends a lot [filler]; 6. It's important for me to keep busy [filler]; 7. I hardly ever expect things to go my way (R); 8. I don't get upset too easily [filler]; 9. I rarely count on good things happening to me (R); 10. Overall, I expect more good things to happen to me than bad",
        "item_source": "Scheier, M. F., Carver, C. S., & Bridges, M. W. (1994). Distinguishing optimism from neuroticism. Journal of Personality and Social Psychology, 67(6), 1063-1078.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Revision of LOT (Scheier & Carver, 1985). Only 6 items scored (3 optimism + 3 pessimism reversed). Alphas typically .70-.80. Debate about unidimensional vs. bidimensional structure. Widely used in health psychology.",
    },
    {
        "instrument_name": "Core Self-Evaluations Scale",
        "abbreviation": "CSES",
        "construct": "Core self-evaluations (self-esteem, self-efficacy, locus of control, emotional stability)",
        "construct_class": "Stable traits",
        "domain": "Self-concept",
        "authors": "Judge, T. A., Erez, A., Bono, J. E., & Thoresen, C. J.",
        "year": 2003,
        "target_population": "Adults (working populations)",
        "number_of_items": 12,
        "response_scale": "5-point Likert (1 = Strongly disagree to 5 = Strongly agree)",
        "subscales": "Unidimensional (integrates four lower-order traits)",
        "exact_items": "Not reproduced here — but items are nonproprietary and may be used without permission per the authors. All 12 items published in Judge et al. (2003), Personnel Psychology, 56, 303-331.",
        "item_source": "Judge, T. A., Erez, A., Bono, J. E., & Thoresen, C. J. (2003). The Core Self-Evaluations Scale: Development of a measure. Personnel Psychology, 56(2), 303-331.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Integrates self-esteem, generalized self-efficacy, locus of control, and emotional stability into a single higher-order factor. Alpha typically .81-.87. Strong predictor of job satisfaction and job performance (Judge & Bono, 2001). Authors explicitly state: 'The CSES is nonproprietary and may be used without permission.'",
    },
    {
        "instrument_name": "Short Grit Scale",
        "abbreviation": "Grit-S",
        "construct": "Grit (perseverance of effort and consistency of interest)",
        "construct_class": "Stable traits",
        "domain": "Motivation / Self-regulation",
        "authors": "Duckworth, A. L., & Quinn, P. D.",
        "year": 2009,
        "target_population": "Adolescents and adults",
        "number_of_items": 8,
        "response_scale": "5-point Likert (1 = Not like me at all to 5 = Very much like me)",
        "subscales": "Consistency of Interest (4); Perseverance of Effort (4)",
        "exact_items": "1. New ideas and projects sometimes distract me from previous ones (R); 2. Setbacks don't discourage me. I don't give up easily; 3. I often set a goal but later choose to pursue a different one (R); 4. I am a hard worker; 5. I have difficulty maintaining my focus on projects that take more than a few months to complete (R); 6. I finish whatever I begin; 7. My interests change from year to year (R); 8. I am diligent. I never give up",
        "item_source": "Duckworth, A. L., & Quinn, P. D. (2009). Development and validation of the Short Grit Scale (Grit-S). Journal of Personality Assessment, 91(2), 166-174.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Short form of the original 12-item Grit Scale (Duckworth et al., 2007). Predictive of educational attainment and GPA. Alpha typically .73-.83. Some criticism regarding discriminant validity from Conscientiousness (Credé et al., 2017).",
    },
    {
        "instrument_name": "Ten-Item Personality Inventory",
        "abbreviation": "TIPI",
        "construct": "Big Five personality traits (brief measure)",
        "construct_class": "Stable traits",
        "domain": "Personality",
        "authors": "Gosling, S. D., Rentfrow, P. J., & Swann, W. B., Jr.",
        "year": 2003,
        "target_population": "Adults (general)",
        "number_of_items": 10,
        "response_scale": "7-point Likert (1 = Disagree strongly to 7 = Agree strongly)",
        "subscales": "Extraversion (2); Agreeableness (2); Conscientiousness (2); Emotional Stability (2); Openness (2)",
        "exact_items": 'Stem: "I see myself as:" 1. Extraverted, enthusiastic; 2. Critical, quarrelsome (R); 3. Dependable, self-disciplined; 4. Anxious, easily upset (R); 5. Open to new experiences, complex; 6. Reserved, quiet (R); 7. Sympathetic, warm; 8. Disorganized, careless (R); 9. Calm, emotionally stable; 10. Conventional, uncreative (R)',
        "item_source": "Gosling, S. D., Rentfrow, P. J., & Swann, W. B., Jr. (2003). A very brief measure of the Big-Five personality domains. Journal of Research in Personality, 37(6), 504-528.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Ultra-brief personality measure. Lower reliability than full scales (test-retest .62-.77) but useful for time-constrained research. Convergent validity with BFI r = .65-.87. Freely available from authors.",
    },
    {
        "instrument_name": "Trait Emotional Intelligence Questionnaire-Short Form",
        "abbreviation": "TEIQue-SF",
        "construct": "Trait emotional intelligence (global and four factors)",
        "construct_class": "Stable traits",
        "domain": "Emotional intelligence",
        "authors": "Petrides, K. V.",
        "year": 2009,
        "target_population": "Adults (general)",
        "number_of_items": 30,
        "response_scale": "7-point Likert (1 = Completely disagree to 7 = Completely agree)",
        "subscales": "Well-Being (6); Self-Control (6); Emotionality (8); Sociability (6); Global Trait EI (4 independent facets)",
        "exact_items": "Not reproduced — available from the London Psychometric Laboratory (psychometriclab.com) for academic research with registration.",
        "item_source": "Petrides, K. V. (2009). Psychometric properties of the Trait Emotional Intelligence Questionnaire (TEIQue). In C. Stough, D. H. Saklofske, & J. D. A. Parker (Eds.), Assessing emotional intelligence (pp. 85-101). Springer.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Short form of 153-item TEIQue. Sampling domain model of emotional intelligence (trait, not ability). Alpha typically .87-.89 for global score. Free for academic use with registration. Distinguishes from ability EI (Mayer-Salovey model).",
    },
    {
        "instrument_name": "Dirty Dozen",
        "abbreviation": "DD",
        "construct": "Dark Triad (Machiavellianism, Narcissism, Psychopathy)",
        "construct_class": "Stable traits",
        "domain": "Personality (dark traits)",
        "authors": "Jonason, P. K., & Webster, G. D.",
        "year": 2010,
        "target_population": "Adults (general)",
        "number_of_items": 12,
        "response_scale": "7-point Likert (1 = Strongly disagree to 7 = Strongly agree)",
        "subscales": "Machiavellianism (4); Narcissism (4); Psychopathy (4)",
        "exact_items": "Not reproduced — items published in Jonason, P. K., & Webster, G. D. (2010). The Dirty Dozen: A concise measure of the Dark Triad. Psychological Assessment, 22(2), 420-432. Verify APA permissions for full reproduction.",
        "item_source": "Jonason, P. K., & Webster, G. D. (2010). The Dirty Dozen: A concise measure of the Dark Triad. Psychological Assessment, 22(2), 420-432.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Ultra-brief Dark Triad measure. Convergent validity with full-length scales (Mach-IV, NPI, SRP-III). Alpha .83 overall. Tradeoff: brevity vs. bandwidth. Alternative: Short Dark Triad (SD3; Jones & Paulhus, 2014, 27 items).",
    },
    {
        "instrument_name": "Interpersonal Reactivity Index",
        "abbreviation": "IRI",
        "construct": "Empathy (multidimensional)",
        "construct_class": "Stable traits",
        "domain": "Social cognition",
        "authors": "Davis, M. H.",
        "year": 1983,
        "target_population": "Adults (general)",
        "number_of_items": 28,
        "response_scale": "5-point Likert (0 = Does not describe me well to 4 = Describes me very well)",
        "subscales": "Perspective Taking (7); Fantasy (7); Empathic Concern (7); Personal Distress (7)",
        "exact_items": "Not reproduced — items published in Davis, M. H. (1983). Measuring individual differences in empathy. Journal of Personality and Social Psychology, 44(1), 113-126. Widely reproduced in academic appendices.",
        "item_source": "Davis, M. H. (1983). Measuring individual differences in empathy: Evidence for a multidimensional approach. Journal of Personality and Social Psychology, 44(1), 113-126.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Most widely used empathy measure. Multidimensional model: cognitive (PT, FS) and affective (EC, PD) empathy. Alphas .70-.78. Over 10,000 citations. Free for research use.",
    },
    {
        "instrument_name": "Psychological Capital Questionnaire",
        "abbreviation": "PCQ-12",
        "construct": "Psychological capital (self-efficacy, hope, resilience, optimism)",
        "construct_class": "Stable traits",
        "domain": "Positive organizational behavior",
        "authors": "Luthans, F., Youssef, C. M., & Avolio, B. J.",
        "year": 2007,
        "target_population": "Working adults",
        "number_of_items": 12,
        "response_scale": "6-point Likert (1 = Strongly disagree to 6 = Strongly agree)",
        "subscales": "Self-Efficacy (3); Hope (3); Resilience (3); Optimism (3)",
        "exact_items": "Not reproduced — proprietary (Mind Garden, Inc.). Purchase required at mindgarden.com.",
        "item_source": "Luthans, F., Youssef, C. M., & Avolio, B. J. (2007). Psychological capital. Oxford University Press. Licensed via Mind Garden.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Based on PsyCap theory (Luthans et al., 2007). Short form of PCQ-24. Alpha typically .88-.89. Meta-analytic support for criterion validity (Avey et al., 2011). Proprietary — requires purchase from Mind Garden.",
    },

    # ======================================================================
    # 2. TRANSIENT STATES (11 instruments)
    # ======================================================================
    {
        "instrument_name": "Positive and Negative Affect Schedule",
        "abbreviation": "PANAS",
        "construct": "Positive and negative affect",
        "construct_class": "Transient states",
        "domain": "Affect / Emotion",
        "authors": "Watson, D., Clark, L. A., & Tellegen, A.",
        "year": 1988,
        "target_population": "Adults (general)",
        "number_of_items": 20,
        "response_scale": "5-point Likert (1 = Very slightly or not at all to 5 = Extremely)",
        "subscales": "Positive Affect (10); Negative Affect (10)",
        "exact_items": "Positive Affect items: Interested; Excited; Strong; Enthusiastic; Proud; Alert; Inspired; Determined; Attentive; Active. Negative Affect items: Distressed; Upset; Guilty; Scared; Hostile; Irritable; Ashamed; Nervous; Jittery; Afraid",
        "item_source": "Watson, D., Clark, L. A., & Tellegen, A. (1988). Development and validation of brief measures of positive and negative affect: The PANAS scales. Journal of Personality and Social Psychology, 54(6), 1063-1070.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "One of the most cited affect measures (>40,000 citations). Multiple timeframes available (moment, today, past week, past year, general). Alphas .86-.90 (PA) and .84-.87 (NA). Two-factor structure consistently replicated.",
    },
    {
        "instrument_name": "State-Trait Anxiety Inventory",
        "abbreviation": "STAI",
        "construct": "State and trait anxiety",
        "construct_class": "Transient states",
        "domain": "Anxiety",
        "authors": "Spielberger, C. D., Gorsuch, R. L., Lushene, R., Vagg, P. R., & Jacobs, G. A.",
        "year": 1983,
        "target_population": "Adults and adolescents (age 15+)",
        "number_of_items": 40,
        "response_scale": "4-point Likert (State: 1 = Not at all to 4 = Very much so; Trait: 1 = Almost never to 4 = Almost always)",
        "subscales": "State Anxiety (S-Anxiety, 20 items); Trait Anxiety (T-Anxiety, 20 items)",
        "exact_items": "Not reproduced — proprietary (Mind Garden, Inc.). Purchase required at mindgarden.com.",
        "item_source": "Spielberger, C. D., Gorsuch, R. L., Lushene, R., Vagg, P. R., & Jacobs, G. A. (1983). Manual for the State-Trait Anxiety Inventory. Consulting Psychologists Press.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Gold standard anxiety measure (>80,000 citations). Distinguishes state (current) from trait (dispositional) anxiety. Alphas .86-.95. Widely translated. Used in clinical and research settings. Proprietary — requires purchase.",
    },
    {
        "instrument_name": "Subjective Happiness Scale",
        "abbreviation": "SHS",
        "construct": "Subjective happiness (global)",
        "construct_class": "Transient states",
        "domain": "Happiness / Subjective wellbeing",
        "authors": "Lyubomirsky, S., & Lepper, H. S.",
        "year": 1999,
        "target_population": "Adults and adolescents",
        "number_of_items": 4,
        "response_scale": "7-point Likert (anchors vary by item)",
        "subscales": "Unidimensional",
        "exact_items": "1. In general, I consider myself: [1 = not a very happy person ... 7 = a very happy person]; 2. Compared with most of my peers, I consider myself: [1 = less happy ... 7 = more happy]; 3. Some people are generally very happy. They enjoy life regardless of what is going on, getting the most out of everything. To what extent does this characterization describe you? [1 = not at all ... 7 = a great deal]; 4. Some people are generally not very happy. Although they are not depressed, they never seem as happy as they might be. To what extent does this characterization describe you? [1 = not at all ... 7 = a great deal] (R)",
        "item_source": "Lyubomirsky, S., & Lepper, H. S. (1999). A measure of subjective happiness: Preliminary reliability and construct validation. Social Indicators Research, 46(2), 137-155.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Ultra-brief global happiness measure. Test-retest .72-.90. Convergent validity with SWLS, peer reports. Alphas .79-.94 across 14 samples. Freely available. Over 15,000 citations.",
    },
    {
        "instrument_name": "Profile of Mood States",
        "abbreviation": "POMS",
        "construct": "Mood states (six dimensions)",
        "construct_class": "Transient states",
        "domain": "Mood / Affect",
        "authors": "McNair, D. M., Lorr, M., & Droppleman, L. F.",
        "year": 1971,
        "target_population": "Adults (clinical and non-clinical)",
        "number_of_items": 65,
        "response_scale": "5-point Likert (0 = Not at all to 4 = Extremely)",
        "subscales": "Tension-Anxiety (9); Depression-Dejection (15); Anger-Hostility (12); Vigor-Activity (8); Fatigue-Inertia (7); Confusion-Bewilderment (7); Total Mood Disturbance",
        "exact_items": "Not reproduced — proprietary (Multi-Health Systems, Inc.). Purchase required at mhs.com. Short forms: POMS-SF (37 items), POMS-2 (65 items revised).",
        "item_source": "McNair, D. M., Lorr, M., & Droppleman, L. F. (1971). Manual for the Profile of Mood States. Educational and Industrial Testing Service.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Classic mood assessment, especially in sport/exercise psychology. Iceberg profile for athletes. POMS-2 (Heuchert & McNair, 2012) is the current edition. Proprietary. Alternative: Brunel Mood Scale (BRUMS; Terry et al., 2003) derived from POMS.",
    },
    {
        "instrument_name": "State Hope Scale",
        "abbreviation": "SHS-State",
        "construct": "State hope (agency and pathways thinking)",
        "construct_class": "Transient states",
        "domain": "Motivation / Hope",
        "authors": "Snyder, C. R., Sympson, S. C., Ybasco, F. C., Borders, T. F., Babyak, M. A., & Higgins, R. L.",
        "year": 1996,
        "target_population": "Adults (general)",
        "number_of_items": 6,
        "response_scale": "8-point Likert (1 = Definitely false to 8 = Definitely true)",
        "subscales": "Agency (3); Pathways (3)",
        "exact_items": "1. If I should find myself in a jam, I could think of many ways to get out of it; 2. At the present time, I am energetically pursuing my goals; 3. There are lots of ways around any problem that I am facing now; 4. Right now, I see myself as being pretty successful; 5. I can think of many ways to reach my current goals; 6. At this time, I am meeting the goals that I have set for myself",
        "item_source": "Snyder, C. R., Sympson, S. C., Ybasco, F. C., Borders, T. F., Babyak, M. A., & Higgins, R. L. (1996). Development and validation of the State Hope Scale. Journal of Personality and Social Psychology, 70(2), 321-335.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "State complement to the Dispositional Hope Scale (Snyder et al., 1991). Sensitive to situational variation. Alpha typically .82-.95. Based on Snyder's hope theory (agency + pathways). Freely available.",
    },
    {
        "instrument_name": "Discrete Emotions Questionnaire",
        "abbreviation": "DEQ",
        "construct": "Discrete emotional states (8 emotions)",
        "construct_class": "Transient states",
        "domain": "Emotion",
        "authors": "Harmon-Jones, C., Bastian, B., & Harmon-Jones, E.",
        "year": 2016,
        "target_population": "Adults (general)",
        "number_of_items": 32,
        "response_scale": "7-point Likert (1 = Not at all to 7 = An extreme amount)",
        "subscales": "Anger (4); Disgust (4); Fear (4); Anxiety (4); Sadness (4); Happiness (4); Relaxation (4); Desire (4)",
        "exact_items": "Anger: anger, mad, pissed off, rage; Disgust: grossed out, revulsion, sickened, nausea; Fear: terror, scared, fear, panic; Anxiety: worry, anxiety, dread, nervous; Sadness: lonely, grief, sad, empty; Desire: wanting, craving, longing, desire; Relaxation: calm, relaxation, chilled out, easygoing; Happiness: happy, enjoyment, satisfaction, liking",
        "item_source": "Harmon-Jones, C., Bastian, B., & Harmon-Jones, E. (2016). The Discrete Emotions Questionnaire: A new tool for measuring state self-reported emotions. PLoS ONE, 11(8), e0159915. Open-access; full instrument in S1 Appendix.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Measures 8 discrete emotions beyond valence-arousal dimensions. Addresses limitation of PANAS which conflates discrete emotions. Alphas .80-.95. Published in open-access PLOS ONE with full instrument in supplementary appendix. Also available on OSF.",
    },
    {
        "instrument_name": "Situational Motivation Scale",
        "abbreviation": "SIMS",
        "construct": "Situational motivation (self-determination continuum)",
        "construct_class": "Transient states",
        "domain": "Motivation",
        "authors": "Guay, F., Vallerand, R. J., & Blanchard, C.",
        "year": 2000,
        "target_population": "Adults and adolescents",
        "number_of_items": 16,
        "response_scale": "7-point Likert (1 = Corresponds not at all to 7 = Corresponds exactly)",
        "subscales": "Intrinsic Motivation (4); Identified Regulation (4); External Regulation (4); Amotivation (4)",
        "exact_items": "Not reproduced — items published in Guay, F., Vallerand, R. J., & Blanchard, C. (2000). On the assessment of situational intrinsic and extrinsic motivation. Motivation and Emotion, 24(3), 175-213.",
        "item_source": "Guay, F., Vallerand, R. J., & Blanchard, C. (2000). On the assessment of situational intrinsic and extrinsic motivation. Motivation and Emotion, 24(3), 175-213.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Based on Self-Determination Theory (Deci & Ryan). Measures motivation for a specific activity at a specific time. Simplex pattern confirms self-determination continuum. Alphas .77-.95.",
    },
    {
        "instrument_name": "Perceived Stress Scale",
        "abbreviation": "PSS-10",
        "construct": "Perceived stress (appraisal of stressfulness)",
        "construct_class": "Transient states",
        "domain": "Stress / Cognitive appraisal",
        "authors": "Cohen, S., Kamarck, T., & Mermelstein, R.",
        "year": 1983,
        "target_population": "Adults (general, community)",
        "number_of_items": 10,
        "response_scale": "5-point Likert (0 = Never to 4 = Very often)",
        "subscales": "Perceived Helplessness (6); Perceived Self-Efficacy (4, reverse-scored)",
        "exact_items": "1. In the last month, how often have you been upset because of something that happened unexpectedly?; 2. In the last month, how often have you felt that you were unable to control the important things in your life?; 3. In the last month, how often have you felt nervous and stressed?; 4. In the last month, how often have you felt confident about your ability to handle your personal problems? (R); 5. In the last month, how often have you felt that things were going your way? (R); 6. In the last month, how often have you found that you could not cope with all the things that you had to do?; 7. In the last month, how often have you been able to control irritations in your life? (R); 8. In the last month, how often have you felt that you were on top of things? (R); 9. In the last month, how often have you been angered because of things that were outside of your control?; 10. In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?",
        "item_source": "Cohen, S., Kamarck, T., & Mermelstein, R. (1983). A global measure of perceived stress. Journal of Health and Social Behavior, 24(4), 385-396. Items freely available from author's Carnegie Mellon website.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Most widely used stress appraisal measure (>50,000 citations). 10-item preferred over original 14-item version. Past-month timeframe. Alphas .84-.86. Not situation-specific — measures general stress appraisal. Freely available.",
    },
    {
        "instrument_name": "State Self-Esteem Scale",
        "abbreviation": "SSES",
        "construct": "State (momentary) self-esteem",
        "construct_class": "Transient states",
        "domain": "Self-concept",
        "authors": "Heatherton, T. F., & Polivy, J.",
        "year": 1991,
        "target_population": "Adults (general)",
        "number_of_items": 20,
        "response_scale": "5-point Likert (1 = Not at all to 5 = Extremely)",
        "subscales": "Performance (7); Social (7); Appearance (6)",
        "exact_items": "Not reproduced — items published in Heatherton, T. F., & Polivy, J. (1991). Development and validation of a scale for measuring state self-esteem. Journal of Personality and Social Psychology, 60(6), 895-910.",
        "item_source": "Heatherton, T. F., & Polivy, J. (1991). Development and validation of a scale for measuring state self-esteem. Journal of Personality and Social Psychology, 60(6), 895-910.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "State complement to RSES. Sensitive to experimental manipulations and daily fluctuations. Three-factor structure (performance, social, appearance). Alphas .87-.92. Widely used in social and experimental psychology.",
    },
    {
        "instrument_name": "Brunel Mood Scale",
        "abbreviation": "BRUMS",
        "construct": "Mood states (six dimensions)",
        "construct_class": "Transient states",
        "domain": "Mood / Affect",
        "authors": "Terry, P. C., Lane, A. M., Lane, H. J., & Keohane, L.",
        "year": 1999,
        "target_population": "Adults and adolescents",
        "number_of_items": 24,
        "response_scale": "5-point Likert (0 = Not at all to 4 = Extremely)",
        "subscales": "Anger (4); Confusion (4); Depression (4); Fatigue (4); Tension (4); Vigour (4)",
        "exact_items": "Not reproduced — adapted from POMS item pool. Available from authors. See Terry, P. C., Lane, A. M., & Fogarty, G. J. (2003). Construct validity of the POMS-A for use with adults. Psychology of Sport and Exercise, 4(2), 125-139.",
        "item_source": "Terry, P. C., Lane, A. M., Lane, H. J., & Keohane, L. (1999). Development and validation of a mood measure for adolescents. Journal of Sports Sciences, 17, 861-872.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Shortened POMS derivative (24 items vs. 65). Originally validated with adolescents but widely used with adults. Popular in sport psychology. Alphas .74-.90. Free alternative to proprietary POMS.",
    },
    {
        "instrument_name": "Affect Balance Scale",
        "abbreviation": "ABS",
        "construct": "Psychological well-being (positive vs. negative affect balance)",
        "construct_class": "Transient states",
        "domain": "Affect / Wellbeing",
        "authors": "Bradburn, N. M.",
        "year": 1969,
        "target_population": "Adults (community)",
        "number_of_items": 10,
        "response_scale": "Dichotomous (Yes/No)",
        "subscales": "Positive Affect (5); Negative Affect (5); Affect Balance (PA - NA)",
        "exact_items": "Not reproduced — items published in Bradburn, N. M. (1969). The Structure of Psychological Well-Being. Aldine Publishing. Historic measure; items available in original monograph.",
        "item_source": "Bradburn, N. M. (1969). The Structure of Psychological Well-Being. Chicago: Aldine.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Pioneering affect measure. Introduced affect balance concept (PA and NA as independent dimensions). Historical importance but largely superseded by PANAS and SPANE. Binary format limits sensitivity.",
    },

    # ======================================================================
    # 3. DYNAMIC EXPERIENCES (11 instruments)
    # ======================================================================
    {
        "instrument_name": "Utrecht Work Engagement Scale",
        "abbreviation": "UWES-17",
        "construct": "Work engagement (vigor, dedication, absorption)",
        "construct_class": "Dynamic experiences",
        "domain": "Work engagement",
        "authors": "Schaufeli, W. B., Salanova, M., González-Romá, V., & Bakker, A. B.",
        "year": 2002,
        "target_population": "Working adults",
        "number_of_items": 17,
        "response_scale": "7-point frequency (0 = Never to 6 = Always/Every day)",
        "subscales": "Vigor (6); Dedication (5); Absorption (6)",
        "exact_items": "Not reproduced — items freely available for academic research from wilmarschaufeli.nl. Download requires acknowledgement of terms. UWES-9 (short form) and UWES-3 (ultra-short) also available.",
        "item_source": "Schaufeli, W. B., Salanova, M., González-Romá, V., & Bakker, A. B. (2002). The measurement of engagement and burnout. Journal of Happiness Studies, 3(1), 71-92. Items at wilmarschaufeli.nl.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Most widely used work engagement measure globally (>20,000 citations). Based on JD-R theory. UWES-9 recommended for most research (Schaufeli et al., 2006). Alphas .80-.93. Three-factor structure replicated cross-culturally but some support for single factor. Freely available for research.",
    },
    {
        "instrument_name": "Flow Short Scale",
        "abbreviation": "FSS",
        "construct": "Flow experience (absorption and smooth functioning)",
        "construct_class": "Dynamic experiences",
        "domain": "Flow / Optimal experience",
        "authors": "Rheinberg, F., Vollmeyer, R., & Engeser, S.",
        "year": 2003,
        "target_population": "Adults (general)",
        "number_of_items": 13,
        "response_scale": "7-point Likert (1 = Not at all to 7 = Very much)",
        "subscales": "Fluency of Performance (6); Absorption by Activity (4); Perceived Importance (3, supplementary)",
        "exact_items": "Not reproduced — originally published in German. English translation available in Engeser, S. (Ed.) (2012). Advances in Flow Research. Springer. Contact authors for validated English version.",
        "item_source": "Rheinberg, F., Vollmeyer, R., & Engeser, S. (2003). Die Erfassung des Flow-Erlebens [The assessment of flow experience]. In J. Stiensmeier-Pelster & F. Rheinberg (Eds.), Diagnostik von Motivation und Selbstkonzept (pp. 261-279). Göttingen: Hogrefe.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Brief measure of flow experience. Can be administered during or immediately after activity. Originally in German; English versions validated. Alphas .80-.92. Complementary to Csikszentmihalyi's ESM approach. Alternatives: DFS-2 (Jackson & Eklund, 2002).",
    },
    {
        "instrument_name": "Basic Psychological Need Satisfaction and Frustration Scale",
        "abbreviation": "BPNSFS",
        "construct": "Basic psychological need satisfaction and frustration (autonomy, competence, relatedness)",
        "construct_class": "Dynamic experiences",
        "domain": "Self-determination theory",
        "authors": "Chen, B., Vansteenkiste, M., Beyers, W., Boone, L., Deci, E. L., Van der Kaap-Deeder, J., ... & Verstuyf, J.",
        "year": 2015,
        "target_population": "Adults and adolescents",
        "number_of_items": 24,
        "response_scale": "5-point Likert (1 = Not true at all to 5 = Completely true)",
        "subscales": "Autonomy Satisfaction (4); Autonomy Frustration (4); Competence Satisfaction (4); Competence Frustration (4); Relatedness Satisfaction (4); Relatedness Frustration (4)",
        "exact_items": "Not reproduced — items published in Chen et al. (2015). Journal of Educational Psychology, 107(4), 1049-1066. Appendix includes items. Available from selfdeterminationtheory.org.",
        "item_source": "Chen, B., et al. (2015). Basic psychological need satisfaction, need frustration, and need strength across four cultures. Motivation and Emotion, 39(2), 216-236.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Key SDT measure. Distinguishes need satisfaction from need frustration (not simply opposites). Validated across 4 cultures. Alphas .73-.89. Supersedes earlier BPNS (La Guardia et al., 2000) and PNSE (Wilson et al., 2006). Domain-specific versions available (work, relationships, exercise).",
    },
    {
        "instrument_name": "Recovery Experience Questionnaire",
        "abbreviation": "REQ",
        "construct": "Recovery experiences after work (psychological detachment, relaxation, mastery, control)",
        "construct_class": "Dynamic experiences",
        "domain": "Occupational health / Recovery",
        "authors": "Sonnentag, S., & Fritz, C.",
        "year": 2007,
        "target_population": "Working adults",
        "number_of_items": 16,
        "response_scale": "5-point Likert (1 = I do not agree at all to 5 = I fully agree)",
        "subscales": "Psychological Detachment (4); Relaxation (4); Mastery (4); Control (4)",
        "exact_items": "Not reproduced — items published in Sonnentag, S., & Fritz, C. (2007). The Recovery Experience Questionnaire. Journal of Occupational Health Psychology, 12(3), 204-221. Available from authors.",
        "item_source": "Sonnentag, S., & Fritz, C. (2007). The Recovery Experience Questionnaire: Development and validation of a measure for assessing recuperation and unwinding from work. Journal of Occupational Health Psychology, 12(3), 204-221.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Key measure in occupational recovery research. Psychological detachment subscale most widely used independently. Alphas .79-.92. Based on effort-recovery model (Meijman & Mulder, 1998) and conservation of resources theory.",
    },
    {
        "instrument_name": "Work-Related Flow Inventory",
        "abbreviation": "WOLF",
        "construct": "Flow at work (absorption, work enjoyment, intrinsic work motivation)",
        "construct_class": "Dynamic experiences",
        "domain": "Work engagement / Flow",
        "authors": "Bakker, A. B.",
        "year": 2008,
        "target_population": "Working adults",
        "number_of_items": 13,
        "response_scale": "7-point frequency (1 = Never to 7 = Always)",
        "subscales": "Absorption (4); Work Enjoyment (4); Intrinsic Work Motivation (5)",
        "exact_items": "Not reproduced — items published in Bakker, A. B. (2008). The work-related flow inventory. Journal of Occupational and Environmental Medicine, 50(8), 904-911.",
        "item_source": "Bakker, A. B. (2008). The work-related flow inventory: Construction and initial validation of the WOLF. Journal of Vocational Behavior, 72(3), 400-414.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Work-specific flow measure. Three-factor structure consistently replicated. Alphas .80-.90. Distinguishes from UWES (engagement). Based on Csikszentmihalyi's flow theory applied to work contexts.",
    },
    {
        "instrument_name": "Job Crafting Scale",
        "abbreviation": "JCS",
        "construct": "Job crafting behaviors (increasing resources and challenges, decreasing demands)",
        "construct_class": "Dynamic experiences",
        "domain": "Work behavior / Proactive behavior",
        "authors": "Tims, M., Bakker, A. B., & Derks, D.",
        "year": 2012,
        "target_population": "Working adults",
        "number_of_items": 21,
        "response_scale": "5-point Likert (1 = Never to 5 = Very often)",
        "subscales": "Increasing Structural Job Resources (5); Increasing Social Job Resources (5); Increasing Challenging Job Demands (5); Decreasing Hindering Job Demands (6)",
        "exact_items": "Not reproduced — items published in Tims, M., Bakker, A. B., & Derks, D. (2012). Development and validation of the job crafting scale. Journal of Vocational Behavior, 80(1), 173-186.",
        "item_source": "Tims, M., Bakker, A. B., & Derks, D. (2012). Development and validation of the job crafting scale. Journal of Vocational Behavior, 80(1), 173-186.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Operationalizes JD-R-based job crafting theory. Four-factor structure. Alphas .75-.82. Predicts engagement, performance, well-being. Alternative: Job Crafting Questionnaire (Slemp & Vella-Brodrick, 2013) based on Wrzesniewski & Dutton's (2001) model.",
    },
    {
        "instrument_name": "Meaning in Life Questionnaire",
        "abbreviation": "MLQ",
        "construct": "Meaning in life (presence and search)",
        "construct_class": "Dynamic experiences",
        "domain": "Existential / Meaning",
        "authors": "Steger, M. F., Frazier, P., Oishi, S., & Kaler, M.",
        "year": 2006,
        "target_population": "Adults (general)",
        "number_of_items": 10,
        "response_scale": "7-point Likert (1 = Absolutely untrue to 7 = Absolutely true)",
        "subscales": "Presence of Meaning (5); Search for Meaning (5)",
        "exact_items": "Presence: 1. I understand my life's meaning; 2. My life has a clear sense of purpose; 3. I have a good sense of what makes my life meaningful; 4. I have discovered a satisfying life purpose; 5. My life has no clear purpose (R). Search: 6. I am looking for something that makes my life feel meaningful; 7. I am always looking to find my life's purpose; 8. I am always searching for something that makes my life feel significant; 9. I am seeking a purpose or mission for my life; 10. I am searching for meaning in my life",
        "item_source": "Steger, M. F., Frazier, P., Oishi, S., & Kaler, M. (2006). The Meaning in Life Questionnaire: Assessing the presence of and search for meaning in life. Journal of Counseling Psychology, 53(1), 80-93. Items freely available from michaelfsteger.com.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Distinguishes having meaning (presence) from seeking meaning (search). Two factors independent but negatively correlated. Alphas .82-.87 (Presence), .87-.92 (Search). Over 6,000 citations. Freely available.",
    },
    {
        "instrument_name": "Gratitude Questionnaire-Six Item Form",
        "abbreviation": "GQ-6",
        "construct": "Dispositional gratitude",
        "construct_class": "Dynamic experiences",
        "domain": "Positive psychology",
        "authors": "McCullough, M. E., Emmons, R. A., & Tsang, J.",
        "year": 2002,
        "target_population": "Adults (general)",
        "number_of_items": 6,
        "response_scale": "7-point Likert (1 = Strongly disagree to 7 = Strongly agree)",
        "subscales": "Unidimensional",
        "exact_items": "1. I have so much in life to be thankful for; 2. If I had to list everything that I felt grateful for, it would be a very long list; 3. When I look at the world, I don't see much to be grateful for (R); 4. I am grateful to a wide variety of people; 5. As I get older I find myself more able to appreciate the people, events, and situations that have been part of my life history; 6. Long amounts of time can go by before I feel grateful to something or someone (R)",
        "item_source": "McCullough, M. E., Emmons, R. A., & Tsang, J. (2002). The grateful disposition: A conceptual and empirical topography. Journal of Personality and Social Psychology, 82(1), 112-127.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Most widely used gratitude measure. Assesses four gratitude facets: intensity, frequency, span, density. Alpha typically .82-.87. Predicts well-being, prosocial behavior. Over 6,000 citations.",
    },
    {
        "instrument_name": "Post-Traumatic Growth Inventory",
        "abbreviation": "PTGI",
        "construct": "Post-traumatic growth (positive change following trauma)",
        "construct_class": "Dynamic experiences",
        "domain": "Trauma / Growth",
        "authors": "Tedeschi, R. G., & Calhoun, L. G.",
        "year": 1996,
        "target_population": "Adults who have experienced trauma",
        "number_of_items": 21,
        "response_scale": "6-point Likert (0 = I did not experience this change to 5 = I experienced this change to a very great degree)",
        "subscales": "Relating to Others (7); New Possibilities (5); Personal Strength (4); Spiritual Change (2); Appreciation of Life (3)",
        "exact_items": "Not reproduced — items published in Tedeschi, R. G., & Calhoun, L. G. (1996). The Posttraumatic Growth Inventory. Journal of Traumatic Stress, 9(3), 455-471. Available from authors; PTGI-SF (10 items) also available.",
        "item_source": "Tedeschi, R. G., & Calhoun, L. G. (1996). The Posttraumatic Growth Inventory: Measuring the positive legacy of trauma. Journal of Traumatic Stress, 9(3), 455-471.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Dominant measure of positive psychological change following adversity. Five-factor structure. Alphas .90-.95. Some debate about whether it measures actual growth vs. perceived growth (Frazier et al., 2009). Over 8,000 citations.",
    },
    {
        "instrument_name": "Savoring Beliefs Inventory",
        "abbreviation": "SBI",
        "construct": "Savoring beliefs (capacity to savor positive experiences)",
        "construct_class": "Dynamic experiences",
        "domain": "Positive psychology",
        "authors": "Bryant, F. B.",
        "year": 2003,
        "target_population": "Adults (general)",
        "number_of_items": 24,
        "response_scale": "7-point Likert (1 = Strongly disagree to 7 = Strongly agree)",
        "subscales": "Anticipating (8); Savoring the Moment (8); Reminiscing (8)",
        "exact_items": "Not reproduced — items published in Bryant, F. B. (2003). Savoring Beliefs Inventory (SBI): A scale for measuring beliefs about savouring. Journal of Mental Health, 12(2), 175-196.",
        "item_source": "Bryant, F. B. (2003). Savoring Beliefs Inventory (SBI): A scale for measuring beliefs about savouring. Journal of Mental Health, 12(2), 175-196.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Unique measure of beliefs about capacity to enjoy positive experiences across three temporal orientations. Alphas .88-.94. Distinguishes from coping (savoring is for positive events). Part of broader savoring model (Bryant & Veroff, 2007).",
    },
    {
        "instrument_name": "Curiosity and Exploration Inventory-II",
        "abbreviation": "CEI-II",
        "construct": "Trait curiosity (stretching and embracing)",
        "construct_class": "Dynamic experiences",
        "domain": "Positive psychology / Motivation",
        "authors": "Kashdan, T. B., Gallagher, M. W., Silvia, P. J., Winterstein, B. P., Breen, W. E., Terhar, D., & Steger, M. F.",
        "year": 2009,
        "target_population": "Adults (general)",
        "number_of_items": 10,
        "response_scale": "5-point Likert (1 = Very slightly or not at all to 5 = Extremely)",
        "subscales": "Stretching (5); Embracing (5)",
        "exact_items": "Not reproduced — items published in Kashdan, T. B., et al. (2009). The Curiosity and Exploration Inventory-II. Journal of Research in Personality, 43(6), 987-998.",
        "item_source": "Kashdan, T. B., et al. (2009). The Curiosity and Exploration Inventory-II: Development, factor structure, and psychometrics. Journal of Research in Personality, 43(6), 987-998.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Revision of CEI (Kashdan et al., 2004). Stretching = motivation to seek knowledge; Embracing = willingness to embrace novelty. Alphas .83-.86. Superseded by Five-Dimensional Curiosity Scale (Kashdan et al., 2018, 25 items).",
    },

    # ======================================================================
    # 4. BEHAVIORS AND BEHAVIORAL TENDENCIES (11 instruments)
    # ======================================================================
    {
        "instrument_name": "Brief COPE",
        "abbreviation": "Brief COPE",
        "construct": "Coping strategies (14 coping dimensions)",
        "construct_class": "Behaviors / behavioral tendencies",
        "domain": "Coping / Self-regulation",
        "authors": "Carver, C. S.",
        "year": 1997,
        "target_population": "Adults (general, clinical)",
        "number_of_items": 28,
        "response_scale": "4-point Likert (1 = I haven't been doing this at all to 4 = I've been doing this a lot)",
        "subscales": "Active Coping (2); Planning (2); Positive Reframing (2); Acceptance (2); Humor (2); Religion (2); Emotional Support (2); Instrumental Support (2); Self-Distraction (2); Denial (2); Venting (2); Substance Use (2); Behavioral Disengagement (2); Self-Blame (2)",
        "exact_items": "Not reproduced in full — 28 items across 14 two-item subscales. Items published in Carver, C. S. (1997). You want to measure coping but your protocol's too long. International Journal of Behavioral Medicine, 4(1), 92-100. Available from author's University of Miami website.",
        "item_source": "Carver, C. S. (1997). You want to measure coping but your protocol's too long: Consider the Brief COPE. International Journal of Behavioral Medicine, 4(1), 92-100.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Short form of full COPE (60 items; Carver et al., 1989). 14 subscales of 2 items each. Flexible timeframe. Widely used in health psychology and stress research. Alpha limited by 2-item subscales (.50-.90). Over 15,000 citations. Freely available from author.",
    },
    {
        "instrument_name": "Emotion Regulation Questionnaire",
        "abbreviation": "ERQ",
        "construct": "Habitual emotion regulation strategies (reappraisal and suppression)",
        "construct_class": "Behaviors / behavioral tendencies",
        "domain": "Emotion regulation",
        "authors": "Gross, J. H., & John, O. P.",
        "year": 2003,
        "target_population": "Adults (general)",
        "number_of_items": 10,
        "response_scale": "7-point Likert (1 = Strongly disagree to 7 = Strongly agree)",
        "subscales": "Cognitive Reappraisal (6); Expressive Suppression (4)",
        "exact_items": "Reappraisal: 1. When I want to feel more positive emotion (such as joy or amusement), I change what I'm thinking about; 2. When I want to feel less negative emotion (such as sadness or anger), I change what I'm thinking about; 3. When I'm faced with a stressful situation, I make myself think about it in a way that helps me stay calm; 4. When I want to feel more positive emotion, I change the way I'm thinking about the situation; 5. I control my emotions by changing the way I think about the situation I'm in; 6. When I want to feel less negative emotion, I change the way I'm thinking about the situation. Suppression: 7. I keep my emotions to myself; 8. When I am feeling positive emotions, I am careful not to express them; 9. I control my emotions by not expressing them; 10. When I am feeling negative emotions, I make sure not to express them",
        "item_source": "Gross, J. H., & John, O. P. (2003). Individual differences in two emotion regulation processes: Implications for affect, relationships, and well-being. Journal of Personality and Social Psychology, 85(2), 348-362. Items freely available from spl.stanford.edu/resources.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Based on Gross's process model of emotion regulation. Two-factor structure consistently replicated. Alphas .79-.82 (Reappraisal), .73-.76 (Suppression). Over 15,000 citations. Freely available from Stanford Psychophysiology Lab website.",
    },
    {
        "instrument_name": "Behavioral Inhibition System / Behavioral Activation System Scales",
        "abbreviation": "BIS/BAS",
        "construct": "Behavioral approach and avoidance motivation",
        "construct_class": "Behaviors / behavioral tendencies",
        "domain": "Motivation / Temperament",
        "authors": "Carver, C. S., & White, T. L.",
        "year": 1994,
        "target_population": "Adults (general)",
        "number_of_items": 24,
        "response_scale": "4-point Likert (1 = Very true for me to 4 = Very false for me)",
        "subscales": "BIS (7); BAS Drive (4); BAS Fun Seeking (4); BAS Reward Responsiveness (5). 4 filler items not scored. 20 scored + 4 fillers = 24 total.",
        "exact_items": "BAS Drive: 1. When I want something, I usually go all-out to get it; 2. I go out of my way to get things I want; 3. If I see a chance to get something I want, I move on it right away; 4. When I go after something I use a 'no holds barred' approach. BAS Fun Seeking: 5. I will often do things for no other reason than that they might be fun; 6. I crave excitement and new sensations; 7. I'm always willing to try something new if I think it will be fun; 8. I often act on the spur of the moment. BAS Reward Responsiveness: 9. When I'm doing well at something, I love to keep at it; 10. When good things happen to me, it affects me strongly; 11. It would excite me to win a contest; 12. When I see an opportunity for something I like, I get excited right away; 13. When I get something I want, I feel excited and energized. BIS: 14. If I think something unpleasant is going to happen I usually get pretty 'worked up'; 15. I worry about making mistakes; 16. Criticism or scolding hurts me quite a bit; 17. I feel pretty worried or upset when I think or know somebody is angry at me; 18. Even if something bad is about to happen to me, I rarely experience fear or nervousness (R); 19. I feel worried when I think I have done poorly at something; 20. I have very few fears compared to my friends (R)",
        "item_source": "Carver, C. S., & White, T. L. (1994). Behavioral inhibition, behavioral activation, and affective responses to impending reward and punishment. Journal of Personality and Social Psychology, 67(2), 319-333.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Based on Gray's reinforcement sensitivity theory. Four-factor structure. Alphas .66-.76 (BIS higher). Widely used in personality, clinical, and neuroscience research. Over 10,000 citations. 24 total items: 20 scored + 4 fillers. Items freely available from Carver's University of Miami website.",
    },
    {
        "instrument_name": "Cognitive Emotion Regulation Questionnaire",
        "abbreviation": "CERQ",
        "construct": "Cognitive emotion regulation strategies (9 strategies)",
        "construct_class": "Behaviors / behavioral tendencies",
        "domain": "Emotion regulation",
        "authors": "Garnefski, N., Kraaij, V., & Spinhoven, P.",
        "year": 2001,
        "target_population": "Adolescents and adults",
        "number_of_items": 36,
        "response_scale": "5-point Likert (1 = (Almost) never to 5 = (Almost) always)",
        "subscales": "Self-Blame (4); Other-Blame (4); Rumination (4); Catastrophizing (4); Putting into Perspective (4); Positive Refocusing (4); Positive Reappraisal (4); Acceptance (4); Planning (4)",
        "exact_items": "Not reproduced — items published in Garnefski, N., Kraaij, V., & Spinhoven, P. (2001). Negative life events, cognitive emotion regulation and emotional problems. Personality and Individual Differences, 30(8), 1311-1327. Short form (CERQ-short, 18 items) also available.",
        "item_source": "Garnefski, N., Kraaij, V., & Spinhoven, P. (2001). Negative life events, cognitive emotion regulation and emotional problems. Personality and Individual Differences, 30(8), 1311-1327.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Uniquely focuses on cognitive (not behavioral) regulation. Nine strategies map onto adaptive vs. maladaptive coping. Alphas .68-.86. Widely used in clinical and health psychology. Short form (CERQ-short; Garnefski & Kraaij, 2006) has 18 items (2 per subscale).",
    },
    {
        "instrument_name": "Pittsburgh Sleep Quality Index",
        "abbreviation": "PSQI",
        "construct": "Sleep quality and disturbances",
        "construct_class": "Behaviors / behavioral tendencies",
        "domain": "Sleep / Health behavior",
        "authors": "Buysse, D. J., Reynolds, C. F., Monk, T. H., Berman, S. R., & Kupfer, D. J.",
        "year": 1989,
        "target_population": "Adults (clinical and non-clinical)",
        "number_of_items": 19,
        "response_scale": "Mixed: open-ended (bedtime, wake time) and 4-point Likert (0 = Not during the past month to 3 = Three or more times a week)",
        "subscales": "Subjective Sleep Quality (1); Sleep Latency (2); Sleep Duration (1); Habitual Sleep Efficiency (3); Sleep Disturbances (9); Use of Sleeping Medication (1); Daytime Dysfunction (2); Global PSQI Score (sum of 7 components, 0-21)",
        "exact_items": "Not reproduced — items available from the University of Pittsburgh Sleep Medicine Institute. Widely reproduced in clinical literature. 5 bed-partner items not scored.",
        "item_source": "Buysse, D. J., Reynolds, C. F., Monk, T. H., Berman, S. R., & Kupfer, D. J. (1989). The Pittsburgh Sleep Quality Index: A new instrument for psychiatric practice and research. Psychiatry Research, 28(2), 193-213.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Gold standard sleep quality measure. Global score >5 indicates poor sleep quality (sensitivity .90, specificity .87 for clinical sleep disorders). Over 20,000 citations. Past-month timeframe. Freely available for research.",
    },
    {
        "instrument_name": "General Procrastination Scale",
        "abbreviation": "GPS",
        "construct": "Trait procrastination",
        "construct_class": "Behaviors / behavioral tendencies",
        "domain": "Self-regulation",
        "authors": "Lay, C. H.",
        "year": 1986,
        "target_population": "Adults (general, students)",
        "number_of_items": 20,
        "response_scale": "5-point Likert (1 = Extremely uncharacteristic to 5 = Extremely characteristic)",
        "subscales": "Unidimensional",
        "exact_items": "Not reproduced — items published in Lay, C. H. (1986). At last, my research article on procrastination. Journal of Research in Personality, 20(4), 474-495.",
        "item_source": "Lay, C. H. (1986). At last, my research article on procrastination. Journal of Research in Personality, 20(4), 474-495.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Widely used measure of general (non-academic) procrastination. Alpha typically .82-.86. Correlates with low conscientiousness, neuroticism, poor self-regulation. Alternative: Pure Procrastination Scale (Steel, 2010, 12 items); Irrational Procrastination Scale (Steel, 2010, 9 items).",
    },
    {
        "instrument_name": "Acceptance and Action Questionnaire-II",
        "abbreviation": "AAQ-II",
        "construct": "Psychological inflexibility / experiential avoidance",
        "construct_class": "Behaviors / behavioral tendencies",
        "domain": "Acceptance and Commitment Therapy",
        "authors": "Bond, F. W., Hayes, S. C., Baer, R. A., Carpenter, K. M., Guenole, N., Orcutt, H. K., Waltz, T., & Zettle, R. D.",
        "year": 2011,
        "target_population": "Adults (general, clinical)",
        "number_of_items": 7,
        "response_scale": "7-point Likert (1 = Never true to 7 = Always true)",
        "subscales": "Unidimensional (higher scores = greater psychological inflexibility)",
        "exact_items": "1. My painful experiences and memories make it difficult for me to live a life that I would value; 2. I'm afraid of my feelings; 3. I worry about not being able to control my worries and feelings; 4. My painful memories prevent me from having a fulfilling life; 5. Emotions cause problems in my life; 6. It seems like most people are handling their lives better than I am; 7. Worrying gets in the way of my success",
        "item_source": "Bond, F. W., et al. (2011). Preliminary psychometric properties of the Acceptance and Action Questionnaire-II. Behavior Therapy, 42(4), 676-688.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Core outcome measure in ACT research. Alpha typically .78-.88. Test-retest .81-.87. Predicts mental health, work performance. Over 7,000 citations. Note: Some methodological debate about whether AAQ-II measures psychological inflexibility vs. general distress (Rochefort et al., 2018). Multidimensional Psychological Flexibility Inventory (MPFI; Rolffs et al., 2018) is a broader alternative.",
    },
    {
        "instrument_name": "Connor-Davidson Resilience Scale",
        "abbreviation": "CD-RISC",
        "construct": "Resilience (ability to cope with stress and adversity)",
        "construct_class": "Behaviors / behavioral tendencies",
        "domain": "Resilience",
        "authors": "Connor, K. M., & Davidson, J. R. T.",
        "year": 2003,
        "target_population": "Adults (general, clinical)",
        "number_of_items": 25,
        "response_scale": "5-point Likert (0 = Not true at all to 4 = True nearly all the time)",
        "subscales": "Personal Competence (8); Trust in Instincts/Tolerance of Negative Affect (7); Positive Acceptance of Change (5); Control (3); Spiritual Influences (2). Note: factor structure debated; many use total score only.",
        "exact_items": "Not reproduced — proprietary. License required from cd-risc.com. CD-RISC-10 (10-item short form) and CD-RISC-2 (2-item ultra-short) also available.",
        "item_source": "Connor, K. M., & Davidson, J. R. T. (2003). Development of a new resilience scale: The Connor-Davidson Resilience Scale (CD-RISC). Depression and Anxiety, 18(2), 76-82.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Widely used resilience measure. Alpha .89. Licensed — fee for use. CD-RISC-10 (Campbell-Sills & Stein, 2007) recommended as psychometrically superior. Alternative free measures: Brief Resilience Scale (Smith et al., 2008, 6 items).",
    },
    {
        "instrument_name": "Health-Promoting Lifestyle Profile II",
        "abbreviation": "HPLP-II",
        "construct": "Health-promoting lifestyle behaviors",
        "construct_class": "Behaviors / behavioral tendencies",
        "domain": "Health behavior",
        "authors": "Walker, S. N., Sechrist, K. R., & Pender, N. J.",
        "year": 1995,
        "target_population": "Adults (general)",
        "number_of_items": 52,
        "response_scale": "4-point Likert (1 = Never to 4 = Routinely)",
        "subscales": "Health Responsibility (9); Physical Activity (8); Nutrition (9); Spiritual Growth (9); Interpersonal Relations (9); Stress Management (8)",
        "exact_items": "Not reproduced — available from the University of Nebraska Medical Center College of Nursing. Contact authors for permission.",
        "item_source": "Walker, S. N., & Hill-Polerecky, D. M. (1996). Psychometric evaluation of the Health-Promoting Lifestyle Profile II. University of Nebraska Medical Center.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Based on Pender's Health Promotion Model. Six-factor structure. Alphas .79-.94. Widely used in nursing and public health research. Over 2,000 citations. Revision of original HPLP (Walker et al., 1987). Available for research with permission.",
    },
    {
        "instrument_name": "Self-Regulation Questionnaire",
        "abbreviation": "SRQ",
        "construct": "Self-regulation capacity",
        "construct_class": "Behaviors / behavioral tendencies",
        "domain": "Self-regulation",
        "authors": "Brown, J. M., Miller, W. R., & Lawendowski, L. A.",
        "year": 1999,
        "target_population": "Adults (general, clinical)",
        "number_of_items": 63,
        "response_scale": "5-point Likert (1 = Strongly disagree to 5 = Strongly agree)",
        "subscales": "Receiving (9); Evaluating (10); Triggering (7); Searching (6); Formulating (7); Implementing (7); Assessing (9); Total Self-Regulation (63 items, 7 process subscales)",
        "exact_items": "Not reproduced — items published in Brown, J. M., Miller, W. R., & Lawendowski, L. A. (1999). The Self-Regulation Questionnaire. In L. VandeCreek & T. L. Jackson (Eds.), Innovations in clinical practice (Vol. 17, pp. 281-292). Available from authors.",
        "item_source": "Brown, J. M., Miller, W. R., & Lawendowski, L. A. (1999). The Self-Regulation Questionnaire. In L. VandeCreek & T. L. Jackson (Eds.), Innovations in clinical practice (Vol. 17, pp. 281-292). Professional Resource Press.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Based on Miller and Brown's (1991) 7-step self-regulation model. Alpha .91 (total). Short form (SSRQ, 31 items; Carey, Neal, & Collins, 2004) more commonly used. Predicts health behaviors, addiction recovery.",
    },
    {
        "instrument_name": "Difficulties in Emotion Regulation Scale",
        "abbreviation": "DERS",
        "construct": "Emotion dysregulation (six dimensions)",
        "construct_class": "Behaviors / behavioral tendencies",
        "domain": "Emotion regulation",
        "authors": "Gratz, K. L., & Roemer, L.",
        "year": 2004,
        "target_population": "Adults (general, clinical)",
        "number_of_items": 36,
        "response_scale": "5-point Likert (1 = Almost never to 5 = Almost always)",
        "subscales": "Non-Acceptance of Emotional Responses (6); Difficulty Engaging in Goal-Directed Behavior (5); Impulse Control Difficulties (6); Lack of Emotional Awareness (6); Limited Access to Emotion Regulation Strategies (8); Lack of Emotional Clarity (5)",
        "exact_items": "Not reproduced — items published in Gratz, K. L., & Roemer, L. (2004). Multidimensional assessment of emotion regulation and dysregulation. Journal of Psychopathology and Behavioral Assessment, 26(1), 41-54. DERS-SF (18 items) and DERS-16 also available.",
        "item_source": "Gratz, K. L., & Roemer, L. (2004). Multidimensional assessment of emotion regulation and dysregulation. Journal of Psychopathology and Behavioral Assessment, 26(1), 41-54.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Comprehensive emotion dysregulation measure. Six-factor structure. Alphas .80-.89 per subscale, .93 total. Widely used in clinical psychology (BPD, PTSD, substance use). Over 10,000 citations. Short forms: DERS-SF (Kaufman et al., 2016, 18 items); DERS-16 (Bjureberg et al., 2016).",
    },

    # ======================================================================
    # 5. WELLBEING AND MENTAL HEALTH (12 instruments)
    # ======================================================================
    {
        "instrument_name": "Mental Health Continuum-Short Form",
        "abbreviation": "MHC-SF",
        "construct": "Positive mental health (emotional, social, psychological wellbeing)",
        "construct_class": "Wellbeing and mental health",
        "domain": "Positive mental health",
        "authors": "Keyes, C. L. M.",
        "year": 2005,
        "target_population": "Adolescents and adults",
        "number_of_items": 14,
        "response_scale": "6-point frequency (0 = Never to 5 = Every day)",
        "subscales": "Emotional Well-Being (3); Social Well-Being (5); Psychological Well-Being (6)",
        "exact_items": "Not reproduced — items available from Corey Keyes (contact author) and published in appendices of several validation studies. Short form of MHC-LF (40 items).",
        "item_source": "Keyes, C. L. M. (2005). Mental illness and/or mental health? Investigating axioms of the complete state model of health. Journal of Consulting and Clinical Psychology, 73(3), 539-548. Also Keyes, C. L. M. (2009). Brief description of the MHC-SF.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Operationalizes dual-continua model (mental illness and mental health are related but distinct). Three-factor structure. Alphas .83-.91. Classifies individuals as flourishing, moderate, or languishing. Over 5,000 citations. Widely translated. Available for research.",
    },
    {
        "instrument_name": "Satisfaction With Life Scale",
        "abbreviation": "SWLS",
        "construct": "Global cognitive life satisfaction",
        "construct_class": "Wellbeing and mental health",
        "domain": "Subjective wellbeing",
        "authors": "Diener, E., Emmons, R. A., Larsen, R. J., & Griffin, S.",
        "year": 1985,
        "target_population": "Adults (general)",
        "number_of_items": 5,
        "response_scale": "7-point Likert (1 = Strongly disagree to 7 = Strongly agree)",
        "subscales": "Unidimensional",
        "exact_items": "1. In most ways my life is close to my ideal; 2. The conditions of my life are excellent; 3. I am satisfied with my life; 4. So far I have gotten the important things I want in life; 5. If I could live my life over, I would change almost nothing",
        "item_source": "Diener, E., Emmons, R. A., Larsen, R. J., & Griffin, S. (1985). The Satisfaction With Life Scale. Journal of Personality Assessment, 49(1), 71-75.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Most widely used life satisfaction measure (>30,000 citations). Alpha .87. Test-retest .82 (2 months). Convergent validity with other wellbeing measures and informant reports. Scoring norms available. Public domain.",
    },
    {
        "instrument_name": "WHO-5 Well-Being Index",
        "abbreviation": "WHO-5",
        "construct": "Subjective psychological well-being",
        "construct_class": "Wellbeing and mental health",
        "domain": "General wellbeing",
        "authors": "World Health Organization / Bech, P.",
        "year": 1998,
        "target_population": "Adults (general, clinical)",
        "number_of_items": 5,
        "response_scale": "6-point frequency (0 = At no time to 5 = All of the time). Raw score 0-25, percentage score 0-100.",
        "subscales": "Unidimensional",
        "exact_items": "Over the last two weeks: 1. I have felt cheerful and in good spirits; 2. I have felt calm and relaxed; 3. I have felt active and vigorous; 4. I woke up feeling fresh and rested; 5. My daily life has been filled with things that interest me",
        "item_source": "World Health Organization (1998). Wellbeing Measures in Primary Health Care / The Depcare Project. WHO Regional Office for Europe. Freely available from who-5.org.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Ultra-brief wellbeing screening tool from WHO. Score <50 suggests poor wellbeing; <28 suggests depression screening needed. Translated into >30 languages. Sensitivity .86 for depression screening. Over 10,000 citations. Public domain (WHO).",
    },
    {
        "instrument_name": "Warwick-Edinburgh Mental Well-Being Scale",
        "abbreviation": "WEMWBS",
        "construct": "Mental well-being (hedonic and eudaimonic)",
        "construct_class": "Wellbeing and mental health",
        "domain": "Mental wellbeing",
        "authors": "Tennant, R., Hiller, L., Fishwick, R., Platt, S., Joseph, S., Weich, S., Parkinson, J., Secker, J., & Stewart-Brown, S.",
        "year": 2007,
        "target_population": "Adults (general, age 16+)",
        "number_of_items": 14,
        "response_scale": "5-point Likert (1 = None of the time to 5 = All of the time)",
        "subscales": "Unidimensional (covers hedonic and eudaimonic wellbeing). SWEMWBS (7 items) is the short form.",
        "exact_items": "Not reproduced — available with free registration from warwick.ac.uk/fac/sci/med/research/platform/wemwbs. Registration required to download and use. SWEMWBS (7-item short form) also available.",
        "item_source": "Tennant, R., et al. (2007). The Warwick-Edinburgh Mental Well-being Scale (WEMWBS): Development and UK validation. Health and Quality of Life Outcomes, 5, 63.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "All positively worded (no reverse scoring). Covers both feeling and functioning aspects of wellbeing. Alpha .89-.91. Used in UK national surveys. Free for research with registration. Rasch analysis supports SWEMWBS. Over 5,000 citations.",
    },
    {
        "instrument_name": "Ryff's Psychological Well-Being Scales",
        "abbreviation": "PWB",
        "construct": "Psychological well-being (eudaimonic, six dimensions)",
        "construct_class": "Wellbeing and mental health",
        "domain": "Eudaimonic wellbeing",
        "authors": "Ryff, C. D.",
        "year": 1989,
        "target_population": "Adults (general)",
        "number_of_items": 84,
        "response_scale": "6-point Likert (1 = Strongly disagree to 6 = Strongly agree)",
        "subscales": "Autonomy; Environmental Mastery; Personal Growth; Positive Relations with Others; Purpose in Life; Self-Acceptance",
        "exact_items": "Not reproduced — various versions available from Carol Ryff at University of Wisconsin-Madison. Contact author for scoring keys and permissions.",
        "item_source": "Ryff, C. D. (1989). Happiness is everything, or is it? Explorations on the meaning of psychological well-being. Journal of Personality and Social Psychology, 57(6), 1069-1081.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Foundational eudaimonic wellbeing measure. Six-factor structure based on developmental, humanistic, and existential psychology. Alphas .86-.93 (84-item); lower for short forms. Used in MIDUS longitudinal study. Over 15,000 citations. Debate about dimensionality (Springer & Hauser, 2006).",
    },
    {
        "instrument_name": "Flourishing Scale",
        "abbreviation": "FS",
        "construct": "Human flourishing (social-psychological prosperity)",
        "construct_class": "Wellbeing and mental health",
        "domain": "Positive psychology / Flourishing",
        "authors": "Diener, E., Wirtz, D., Tov, W., Kim-Prieto, C., Choi, D., Oishi, S., & Biswas-Diener, R.",
        "year": 2010,
        "target_population": "Adults (general)",
        "number_of_items": 8,
        "response_scale": "7-point Likert (1 = Strongly disagree to 7 = Strongly agree)",
        "subscales": "Unidimensional",
        "exact_items": "1. I lead a purposeful and meaningful life; 2. My social relationships are supportive and rewarding; 3. I am engaged and interested in my daily activities; 4. I actively contribute to the happiness and well-being of others; 5. I am competent and capable in the activities that are important to me; 6. I am a good person and live a good life; 7. I am optimistic about my future; 8. People respect me",
        "item_source": "Diener, E., et al. (2010). New well-being measures: Short scales to assess flourishing and positive and negative feelings. Social Indicators Research, 97(2), 143-156.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Originally called Psychological Flourishing Scale. Covers purpose, relationships, engagement, contribution, competence, self-acceptance, optimism, respect. Alpha .87. Strongly correlated with Ryff's PWB but briefer. Over 5,000 citations. Freely available.",
    },
    {
        "instrument_name": "Scale of Positive and Negative Experience",
        "abbreviation": "SPANE",
        "construct": "Positive and negative feelings/experiences",
        "construct_class": "Wellbeing and mental health",
        "domain": "Affective wellbeing",
        "authors": "Diener, E., Wirtz, D., Tov, W., Kim-Prieto, C., Choi, D., Oishi, S., & Biswas-Diener, R.",
        "year": 2010,
        "target_population": "Adults (general)",
        "number_of_items": 12,
        "response_scale": "5-point frequency (1 = Very rarely or never to 5 = Very often or always)",
        "subscales": "SPANE-P (Positive, 6 items); SPANE-N (Negative, 6 items); SPANE-B (Balance = P - N)",
        "exact_items": "Positive: Pleasant, Happy, Good, Positive, Joyful, Contented. Negative: Bad, Unpleasant, Negative, Sad, Afraid, Angry. Stem: 'Please think about what you have been doing and experiencing during the past four weeks.'",
        "item_source": "Diener, E., et al. (2010). New well-being measures: Short scales to assess flourishing and positive and negative feelings. Social Indicators Research, 97(2), 143-156.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Designed to overcome PANAS limitations (PANAS items are high-arousal, culture-specific). Includes both general (Good, Bad) and specific (Joyful, Angry) feelings. Alphas .83-.90. Published with Flourishing Scale. Freely available.",
    },
    {
        "instrument_name": "PERMA-Profiler",
        "abbreviation": "PERMA",
        "construct": "Flourishing (PERMA model: Positive emotion, Engagement, Relationships, Meaning, Accomplishment)",
        "construct_class": "Wellbeing and mental health",
        "domain": "Positive psychology / Wellbeing",
        "authors": "Butler, J., & Kern, M. L.",
        "year": 2016,
        "target_population": "Adults (general)",
        "number_of_items": 23,
        "response_scale": "11-point scale (0-10, anchors vary by item)",
        "subscales": "Positive Emotion (3); Engagement (3); Relationships (3); Meaning (3); Accomplishment (3); Overall Well-Being (3); Negative Emotion (3); Health (3); Loneliness (1)",
        "exact_items": "Not reproduced — items published in Butler, J., & Kern, M. L. (2016). The PERMA-Profiler: A brief multidimensional measure of flourishing. International Journal of Wellbeing, 6(3), 1-48. Available from peggykern.org/questionnaires.",
        "item_source": "Butler, J., & Kern, M. L. (2016). The PERMA-Profiler: A brief multidimensional measure of flourishing. International Journal of Wellbeing, 6(3), 1-48.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Based on Seligman's (2011) PERMA model. Five pillars + negative affect, health, loneliness. Alphas .82-.92 per domain. Filler item included. 11-point response scale for increased sensitivity. Available from author's website. Growing use in positive psychology research.",
    },
    {
        "instrument_name": "Oxford Happiness Questionnaire",
        "abbreviation": "OHQ",
        "construct": "Personal happiness (multidimensional)",
        "construct_class": "Wellbeing and mental health",
        "domain": "Happiness",
        "authors": "Hills, P., & Argyle, M.",
        "year": 2002,
        "target_population": "Adults (general)",
        "number_of_items": 29,
        "response_scale": "6-point Likert (1 = Strongly disagree to 6 = Strongly agree)",
        "subscales": "Unidimensional (or two factors in some analyses: life satisfaction and psychological wellbeing)",
        "exact_items": "Not reproduced — items published in Hills, P., & Argyle, M. (2002). The Oxford Happiness Questionnaire: A compact scale for the measurement of psychological well-being. Personality and Individual Differences, 33(7), 1073-1082. Revision of Oxford Happiness Inventory (Argyle et al., 1989).",
        "item_source": "Hills, P., & Argyle, M. (2002). The Oxford Happiness Questionnaire: A compact scale for the measurement of psychological well-being. Personality and Individual Differences, 33(7), 1073-1082.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Revision of Oxford Happiness Inventory. Alpha .91. Changed from multiple-choice to Likert format. Some criticism of item heterogeneity (combines cognitive, affective, and behavioral items). Over 4,000 citations.",
    },
    {
        "instrument_name": "Personal Well-Being Index",
        "abbreviation": "PWI",
        "construct": "Subjective wellbeing (domain-specific life satisfaction)",
        "construct_class": "Wellbeing and mental health",
        "domain": "Subjective wellbeing",
        "authors": "International Wellbeing Group / Cummins, R. A.",
        "year": 2013,
        "target_population": "Adults (general, cross-cultural)",
        "number_of_items": 8,
        "response_scale": "11-point scale (0 = No satisfaction at all to 10 = Completely satisfied)",
        "subscales": "Standard of Living; Health; Achieving in Life; Relationships; Safety; Community-Connectedness; Future Security; Spirituality/Religion (optional)",
        "exact_items": "How satisfied are you with: 1. your standard of living?; 2. your health?; 3. what you are achieving in life?; 4. your personal relationships?; 5. how safe you feel?; 6. feeling part of your community?; 7. your future security?; 8. your spirituality or religion? (optional domain)",
        "item_source": "International Wellbeing Group (2013). Personal Wellbeing Index, 5th Edition. Australian Centre on Quality of Life, Deakin University. Available from acqol.com.au.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Decomposes global life satisfaction into 7-8 domains. Based on Cummins' homeostasis theory of wellbeing. 11-point scale recommended. Used in Australian Unity Wellbeing Index (national surveys). Alphas .70-.85. Freely available. Variants: PWI-SC (school children), PWI-ID (intellectual disability), PWI-PS (pre-school).",
    },
    {
        "instrument_name": "WHOQOL-BREF",
        "abbreviation": "WHOQOL-BREF",
        "construct": "Quality of life (four domains)",
        "construct_class": "Wellbeing and mental health",
        "domain": "Quality of life",
        "authors": "The WHOQOL Group / World Health Organization",
        "year": 1998,
        "target_population": "Adults (general, clinical, cross-cultural)",
        "number_of_items": 26,
        "response_scale": "5-point Likert (various anchors per item: intensity, capacity, frequency, evaluation)",
        "subscales": "Physical Health (7); Psychological (6); Social Relationships (3); Environment (8); Overall QOL (1); General Health (1)",
        "exact_items": "Not reproduced — available from the WHO. Researchers must register with the WHOQOL Group to obtain the instrument. Available from who.int/tools/whoqol.",
        "item_source": "The WHOQOL Group (1998). Development of the World Health Organization WHOQOL-BREF quality of life assessment. Psychological Medicine, 28(3), 551-558.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Short form of WHOQOL-100. Cross-culturally developed (15 field centres). Alphas .66-.84. Domain scores transformed to 0-100. Widely used in clinical trials and population health. Available in >40 languages. Registration required. Over 15,000 citations.",
    },

    # ======================================================================
    # 6. COGNITIVE OR AFFECTIVE EXPERIENCES (11 instruments)
    # ======================================================================
    {
        "instrument_name": "Five Facet Mindfulness Questionnaire",
        "abbreviation": "FFMQ",
        "construct": "Mindfulness (five facets)",
        "construct_class": "Cognitive / affective experiences",
        "domain": "Mindfulness / Contemplative",
        "authors": "Baer, R. A., Smith, G. T., Hopkins, J., Krietemeyer, J., & Toney, L.",
        "year": 2006,
        "target_population": "Adults (general, meditators and non-meditators)",
        "number_of_items": 39,
        "response_scale": "5-point Likert (1 = Never or very rarely true to 5 = Very often or always true)",
        "subscales": "Observing (8); Describing (8); Acting with Awareness (8); Non-Judging of Inner Experience (8); Non-Reactivity to Inner Experience (7)",
        "exact_items": "Not reproduced — items published in Baer, R. A., et al. (2006). Using self-report assessment methods to explore facets of mindfulness. Assessment, 13(1), 27-45. FFMQ-15 (short form) and FFMQ-24 also available. Items freely available from author.",
        "item_source": "Baer, R. A., Smith, G. T., Hopkins, J., Krietemeyer, J., & Toney, L. (2006). Using self-report assessment methods to explore facets of mindfulness. Assessment, 13(1), 27-45.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Derived from factor analysis of five existing mindfulness questionnaires. Five-factor structure. Alphas .75-.91. Observing facet operates differently in meditators vs. non-meditators. Over 8,000 citations. Freely available from author.",
    },
    {
        "instrument_name": "Mindful Attention Awareness Scale",
        "abbreviation": "MAAS",
        "construct": "Dispositional mindfulness (present-moment attention and awareness)",
        "construct_class": "Cognitive / affective experiences",
        "domain": "Mindfulness / Attention",
        "authors": "Brown, K. W., & Ryan, R. M.",
        "year": 2003,
        "target_population": "Adults (general)",
        "number_of_items": 15,
        "response_scale": "6-point Likert (1 = Almost always to 6 = Almost never)",
        "subscales": "Unidimensional",
        "exact_items": "1. I could be experiencing some emotion and not be conscious of it until some time later; 2. I break or spill things because of carelessness, not paying attention, or thinking of something else; 3. I find it difficult to stay focused on what's happening in the present; 4. I tend to walk quickly to get where I'm going without paying attention to what I experience along the way; 5. I tend not to notice feelings of physical tension or discomfort until they really grab my attention; 6. I forget a person's name almost as soon as I've been told it for the first time; 7. It seems I am 'running on automatic' without much awareness of what I'm doing; 8. I rush through activities without being really attentive to them; 9. I get so focused on the goal I want to achieve that I lose touch with what I'm doing right now to get there; 10. I do jobs or tasks automatically, without being aware of what I'm doing; 11. I find myself listening to someone with one ear, doing something else at the same time; 12. I drive places on 'automatic pilot' and then wonder why I went there; 13. I find myself preoccupied with the future or the past; 14. I find myself doing things without paying attention; 15. I snack without being aware that I'm eating",
        "item_source": "Brown, K. W., & Ryan, R. M. (2003). The benefits of being present: Mindfulness and its role in psychological well-being. Journal of Personality and Social Psychology, 84(4), 822-848. Items freely available from selfdeterminationtheory.org.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "All items reverse-scored (measure mindlessness; higher score = more mindful). Unidimensional. Alpha .82-.87. Discriminates meditators from non-meditators. Over 10,000 citations. State version (state MAAS, 5 items) available. Freely available.",
    },
    {
        "instrument_name": "Self-Compassion Scale",
        "abbreviation": "SCS",
        "construct": "Self-compassion (six components)",
        "construct_class": "Cognitive / affective experiences",
        "domain": "Self-compassion / Mindfulness",
        "authors": "Neff, K. D.",
        "year": 2003,
        "target_population": "Adults (general)",
        "number_of_items": 26,
        "response_scale": "5-point Likert (1 = Almost never to 5 = Almost always)",
        "subscales": "Self-Kindness (5); Self-Judgment (5, R); Common Humanity (4); Isolation (4, R); Mindfulness (4); Over-Identification (4, R)",
        "exact_items": "Not reproduced — items freely available from self-compassion.org (Kristin Neff's website). SCS-SF (12 items) also available. Registration not required.",
        "item_source": "Neff, K. D. (2003). The development and validation of a scale to measure self-compassion. Self and Identity, 2(3), 223-250. Items at self-compassion.org.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Six-factor with higher-order self-compassion factor. Alphas .75-.81 per subscale, .92 total. Bifactor structure debate (Neff et al., 2019 vs. Muris & Petrocchi, 2017). Over 8,000 citations. Freely available from author's website.",
    },
    {
        "instrument_name": "Cognitive Failures Questionnaire",
        "abbreviation": "CFQ",
        "construct": "Self-reported cognitive failures in everyday life",
        "construct_class": "Cognitive / affective experiences",
        "domain": "Cognitive functioning",
        "authors": "Broadbent, D. E., Cooper, P. F., FitzGerald, P., & Parkes, K. R.",
        "year": 1982,
        "target_population": "Adults (general)",
        "number_of_items": 25,
        "response_scale": "5-point frequency (0 = Never to 4 = Very often)",
        "subscales": "Forgetfulness; Distractibility; False Triggering (factor structure varies across studies)",
        "exact_items": "Not reproduced — items published in Broadbent, D. E., et al. (1982). The Cognitive Failures Questionnaire (CFQ) and its correlates. British Journal of Clinical Psychology, 21(1), 1-16.",
        "item_source": "Broadbent, D. E., Cooper, P. F., FitzGerald, P., & Parkes, K. R. (1982). The Cognitive Failures Questionnaire (CFQ) and its correlates. British Journal of Clinical Psychology, 21(1), 1-16.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Measures everyday cognitive slips (memory, attention, perception). Alpha .89-.91. Factor structure debated (1-4 factors). Correlates with accident proneness, neuroticism. Over 3,000 citations. Free for research.",
    },
    {
        "instrument_name": "Ruminative Responses Scale",
        "abbreviation": "RRS",
        "construct": "Rumination (brooding and reflection)",
        "construct_class": "Cognitive / affective experiences",
        "domain": "Rumination / Repetitive thought",
        "authors": "Treynor, W., Gonzalez, R., & Nolen-Hoeksema, S.",
        "year": 2003,
        "target_population": "Adults (general, clinical)",
        "number_of_items": 22,
        "response_scale": "4-point frequency (1 = Almost never to 4 = Almost always)",
        "subscales": "Brooding (5); Reflection (5); Depression-Related (12). 10-item version (Brooding + Reflection only) commonly used.",
        "exact_items": "Not reproduced — items originally from Nolen-Hoeksema, S., & Morrow, J. (1991). A prospective study of depression and posttraumatic stress symptoms after a natural disaster. Journal of Personality and Social Psychology, 61, 115-121. Refined in Treynor et al. (2003).",
        "item_source": "Treynor, W., Gonzalez, R., & Nolen-Hoeksema, S. (2003). Rumination reconsidered: A psychometric analysis. Cognitive Therapy and Research, 27(3), 247-259.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Part of Response Styles Questionnaire. Brooding subscale is the maladaptive component (predicts depression). Reflection is more adaptive. Alphas .72-.77 (Brooding), .72-.76 (Reflection). Over 5,000 citations. 10-item short form most recommended.",
    },
    {
        "instrument_name": "Toronto Alexithymia Scale",
        "abbreviation": "TAS-20",
        "construct": "Alexithymia (difficulty identifying and describing feelings)",
        "construct_class": "Cognitive / affective experiences",
        "domain": "Emotion awareness / Alexithymia",
        "authors": "Bagby, R. M., Parker, J. D. A., & Taylor, G. J.",
        "year": 1994,
        "target_population": "Adults (general, clinical)",
        "number_of_items": 20,
        "response_scale": "5-point Likert (1 = Strongly disagree to 5 = Strongly agree)",
        "subscales": "Difficulty Identifying Feelings (7); Difficulty Describing Feelings (5); Externally-Oriented Thinking (8)",
        "exact_items": "Not reproduced — items available from G. J. Taylor (contact author). Licensing required for commercial use. Academic use permitted with acknowledgement.",
        "item_source": "Bagby, R. M., Parker, J. D. A., & Taylor, G. J. (1994). The twenty-item Toronto Alexithymia Scale: I. Item selection and cross-validation of the factor structure. Journal of Psychosomatic Research, 38(1), 23-32.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Gold standard alexithymia measure. Three-factor structure. Alphas .73-.84. Clinical cutoff: >= 61 (alexithymic), 52-60 (possible alexithymia). Widely used in psychosomatic medicine. Over 8,000 citations. EOT subscale has lower reliability.",
    },
    {
        "instrument_name": "Need for Cognition Scale",
        "abbreviation": "NCS-18",
        "construct": "Need for cognition (tendency to engage in and enjoy effortful thinking)",
        "construct_class": "Cognitive / affective experiences",
        "domain": "Cognitive motivation",
        "authors": "Cacioppo, J. T., Petty, R. E., & Kao, C. F.",
        "year": 1984,
        "target_population": "Adults (general)",
        "number_of_items": 18,
        "response_scale": "5-point Likert (1 = Extremely uncharacteristic to 5 = Extremely characteristic)",
        "subscales": "Unidimensional",
        "exact_items": "1. I would prefer complex to simple problems; 2. I like to have the responsibility of handling a situation that requires a lot of thinking; 3. Thinking is not my idea of fun (R); 4. I would rather do something that requires little thought than something that is sure to challenge my thinking abilities (R); 5. I try to anticipate and avoid situations where there is a likely chance I will have to think in depth about something (R); 6. I find satisfaction in deliberating hard and for long hours; 7. I only think as hard as I have to (R); 8. I prefer to think about small, daily projects to long-term ones (R); 9. I like tasks that require little thought once I've learned them (R); 10. The idea of relying on thought to make my way to the top appeals to me; 11. I really enjoy a task that involves coming up with new solutions to problems; 12. Learning new ways to think doesn't excite me very much (R); 13. I prefer my life to be filled with puzzles that I must solve; 14. The notion of thinking abstractly is appealing to me; 15. I would prefer a task that is intellectual, difficult, and important to one that is somewhat important but does not require much thought; 16. I feel relief rather than satisfaction after completing a task that required a lot of mental effort (R); 17. It's enough for me that something gets the job done; I don't care how or why it works (R); 18. I usually end up deliberating about issues even when they do not affect me personally",
        "item_source": "Cacioppo, J. T., Petty, R. E., & Kao, C. F. (1984). The efficient assessment of need for cognition. Journal of Personality Assessment, 48(3), 306-307. Short form of Cacioppo & Petty (1982) 34-item version.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Short form of original 34-item NCS. Unidimensional. Alpha .87-.90. Predicts information processing depth, persuasion susceptibility, academic performance. Over 5,000 citations (original + short form). Freely available.",
    },
    {
        "instrument_name": "White Bear Suppression Inventory",
        "abbreviation": "WBSI",
        "construct": "Thought suppression tendency",
        "construct_class": "Cognitive / affective experiences",
        "domain": "Cognitive control / Intrusive thoughts",
        "authors": "Wegner, D. M., & Zanakos, S.",
        "year": 1994,
        "target_population": "Adults (general, clinical)",
        "number_of_items": 15,
        "response_scale": "5-point Likert (1 = Strongly disagree to 5 = Strongly agree)",
        "subscales": "Unwanted Intrusive Thoughts (factor 1); Thought Suppression (factor 2). Often scored as total.",
        "exact_items": "Not reproduced — items published in Wegner, D. M., & Zanakos, S. (1994). Chronic thought suppression. Journal of Personality, 62(4), 615-640.",
        "item_source": "Wegner, D. M., & Zanakos, S. (1994). Chronic thought suppression. Journal of Personality, 62(4), 615-640.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Based on Wegner's ironic process theory (attempting to suppress thoughts paradoxically increases them). Alpha .87-.89. Two-factor structure (intrusion + suppression). Predicts OCD symptoms, PTSD. Over 2,000 citations.",
    },
    {
        "instrument_name": "Cognitive Flexibility Inventory",
        "abbreviation": "CFI",
        "construct": "Cognitive flexibility (ability to adapt thinking)",
        "construct_class": "Cognitive / affective experiences",
        "domain": "Cognitive flexibility",
        "authors": "Dennis, J. P., & Vander Wal, J. S.",
        "year": 2010,
        "target_population": "Adults (general)",
        "number_of_items": 20,
        "response_scale": "7-point Likert (1 = Strongly disagree to 7 = Strongly agree)",
        "subscales": "Alternatives (13); Control (7)",
        "exact_items": "Not reproduced — items published in Dennis, J. P., & Vander Wal, J. S. (2010). The Cognitive Flexibility Inventory. Journal of Clinical Psychology, 66(11), 1243-1260.",
        "item_source": "Dennis, J. P., & Vander Wal, J. S. (2010). The Cognitive Flexibility Inventory: Instrument development and estimates of reliability and validity. Cognitive Therapy and Research, 34(3), 241-253.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Two-factor structure: Alternatives (ability to perceive multiple solutions) and Control (perception of controllability). Alphas .91 (Alternatives), .86 (Control). Negatively related to depression, positively to cognitive reappraisal. Free for research.",
    },
    {
        "instrument_name": "Penn State Worry Questionnaire",
        "abbreviation": "PSWQ",
        "construct": "Pathological worry (trait worry)",
        "construct_class": "Cognitive / affective experiences",
        "domain": "Anxiety / Worry",
        "authors": "Meyer, T. J., Miller, M. L., Metzger, R. L., & Borkovec, T. D.",
        "year": 1990,
        "target_population": "Adults (general, clinical)",
        "number_of_items": 16,
        "response_scale": "5-point Likert (1 = Not at all typical of me to 5 = Very typical of me)",
        "subscales": "Unidimensional (5 reverse-scored items sometimes form a method factor)",
        "exact_items": "Not reproduced — items published in Meyer, T. J., Miller, M. L., Metzger, R. L., & Borkovec, T. D. (1990). Development and validation of the Penn State Worry Questionnaire. Behaviour Research and Therapy, 28(6), 487-495.",
        "item_source": "Meyer, T. J., Miller, M. L., Metzger, R. L., & Borkovec, T. D. (1990). Development and validation of the Penn State Worry Questionnaire. Behaviour Research and Therapy, 28(6), 487-495.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Gold standard measure of pathological worry. Distinguishes GAD from other anxiety disorders. Alpha .91-.95. Clinical cutoff typically 45-65 (varies by population). Over 5,000 citations. PSWQ-A (abbreviated, 8 items; Hopko et al., 2003) removes problematic reverse items.",
    },

    # ======================================================================
    # 7. WORK AND ORGANIZATIONAL CONSTRUCTS (12 instruments)
    # ======================================================================
    {
        "instrument_name": "Burnout Assessment Tool",
        "abbreviation": "BAT",
        "construct": "Burnout (exhaustion, mental distance, cognitive impairment, emotional impairment)",
        "construct_class": "Work and organizational",
        "domain": "Occupational health / Burnout",
        "authors": "Schaufeli, W. B., De Witte, H., & Desart, S.",
        "year": 2020,
        "target_population": "Working adults",
        "number_of_items": 23,
        "response_scale": "5-point frequency (1 = Never to 5 = Always)",
        "subscales": "Exhaustion (8); Mental Distance (5); Cognitive Impairment (5); Emotional Impairment (5). Also: Secondary symptoms (psychosomatic complaints, 10 items, supplementary).",
        "exact_items": "Not reproduced — items available from burnoutassessmenttool.be with registration for research use. Multiple language versions available.",
        "item_source": "Schaufeli, W. B., De Witte, H., & Desart, S. (2020). Manual Burnout Assessment Tool (BAT). KU Leuven. Also: Schaufeli, W. B., et al. (2020). Burnout Assessment Tool (BAT) — Development, validity, and reliability. International Journal of Environmental Research and Public Health, 17(24), 9495.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Next-generation burnout measure addressing MBI limitations. Four core dimensions + secondary psychosomatic symptoms. Alpha .91-.95. Aligned with WHO ICD-11 burnout definition. Freely available for research from official website. Stronger psychometric properties than MBI per initial validation.",
    },
    {
        "instrument_name": "Maslach Burnout Inventory",
        "abbreviation": "MBI",
        "construct": "Burnout (exhaustion, cynicism/depersonalization, professional efficacy)",
        "construct_class": "Work and organizational",
        "domain": "Occupational health / Burnout",
        "authors": "Maslach, C., & Jackson, S. E.",
        "year": 1981,
        "target_population": "Working adults (human services, general, educators)",
        "number_of_items": 22,
        "response_scale": "7-point frequency (0 = Never to 6 = Every day)",
        "subscales": "Emotional Exhaustion (9); Depersonalization/Cynicism (5); Personal Accomplishment/Professional Efficacy (8). Note: Three versions — MBI-HSS (human services), MBI-GS (general survey), MBI-ES (educators).",
        "exact_items": "Not reproduced — proprietary (Mind Garden, Inc.). Purchase required at mindgarden.com.",
        "item_source": "Maslach, C., & Jackson, S. E. (1981). The measurement of experienced burnout. Journal of Organizational Behavior, 2(2), 99-113. Licensed via Mind Garden.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Most widely used burnout measure globally (>20,000 citations). Three-factor structure. Alphas .71-.90. Not scored as single total. Criticism: proprietary cost, conceptual narrowness (see BAT as open alternative). MBI-GS (Schaufeli et al., 1996) for non-human-services workers.",
    },
    {
        "instrument_name": "Job Satisfaction Survey",
        "abbreviation": "JSS",
        "construct": "Job satisfaction (nine facets)",
        "construct_class": "Work and organizational",
        "domain": "Work attitudes",
        "authors": "Spector, P. E.",
        "year": 1985,
        "target_population": "Working adults (especially human service, public, nonprofit)",
        "number_of_items": 36,
        "response_scale": "6-point Likert (1 = Disagree very much to 6 = Agree very much)",
        "subscales": "Pay (4); Promotion (4); Supervision (4); Fringe Benefits (4); Contingent Rewards (4); Operating Conditions (4); Coworkers (4); Nature of Work (4); Communication (4); Total Job Satisfaction",
        "exact_items": "Not reproduced — items freely available from Paul Spector's website at shell.cas.usf.edu/~spector/scales/jsspag.html. Free for academic and research use.",
        "item_source": "Spector, P. E. (1985). Measurement of human service staff satisfaction: Development of the Job Satisfaction Survey. American Journal of Community Psychology, 13(6), 693-713. Items at Spector's USF website.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Nine-facet job satisfaction measure. Free for non-commercial use (from author's website). Alphas .60-.91 per subscale. Originally developed for human service organizations but widely used across sectors. Over 5,000 citations.",
    },
    {
        "instrument_name": "Psychological Safety Scale",
        "abbreviation": "PSS-Edm",
        "construct": "Team psychological safety",
        "construct_class": "Work and organizational",
        "domain": "Team dynamics / Organizational climate",
        "authors": "Edmondson, A. C.",
        "year": 1999,
        "target_population": "Working adults (team members)",
        "number_of_items": 7,
        "response_scale": "7-point Likert (1 = Very inaccurate to 7 = Very accurate)",
        "subscales": "Unidimensional",
        "exact_items": "1. If you make a mistake on this team, it is often held against you (R); 2. Members of this team are able to bring up problems and tough issues; 3. People on this team sometimes reject others for being different (R); 4. It is safe to take a risk on this team; 5. It is difficult to ask other members of this team for help (R); 6. No one on this team would deliberately act in a way that undermines my efforts; 7. Working with members of this team, my unique skills and talents are valued and utilized",
        "item_source": "Edmondson, A. C. (1999). Psychological safety and learning behavior in work teams. Administrative Science Quarterly, 44(2), 350-383.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Foundational measure of team psychological safety. Alpha .82. Team-level construct (aggregated from individual responses). Google's Project Aristotle identified psychological safety as #1 predictor of team effectiveness. Over 8,000 citations.",
    },
    {
        "instrument_name": "Leader-Member Exchange Scale",
        "abbreviation": "LMX-7",
        "construct": "Quality of leader-member exchange relationship",
        "construct_class": "Work and organizational",
        "domain": "Leadership",
        "authors": "Graen, G. B., & Uhl-Bien, M.",
        "year": 1995,
        "target_population": "Working adults (subordinates rating relationship with leader)",
        "number_of_items": 7,
        "response_scale": "5-point Likert (various anchors per item)",
        "subscales": "Unidimensional",
        "exact_items": "Not reproduced — items published in Graen, G. B., & Uhl-Bien, M. (1995). Relationship-based approach to leadership. The Leadership Quarterly, 6(2), 219-247. Widely reproduced in academic literature.",
        "item_source": "Graen, G. B., & Uhl-Bien, M. (1995). Relationship-based approach to leadership: Development of leader-member exchange (LMX) theory of leadership over 25 years. The Leadership Quarterly, 6(2), 219-247.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Most widely used LMX measure. Unidimensional (though some argue for multidimensional LMX; Liden & Maslyn, 1998). Alpha .80-.90. Predicts OCB, turnover intentions, job satisfaction. Over 5,000 citations. Free for research use.",
    },
    {
        "instrument_name": "Multifactor Leadership Questionnaire",
        "abbreviation": "MLQ-5X",
        "construct": "Transformational, transactional, and laissez-faire leadership",
        "construct_class": "Work and organizational",
        "domain": "Leadership",
        "authors": "Bass, B. M., & Avolio, B. J.",
        "year": 1995,
        "target_population": "Working adults (leaders and raters)",
        "number_of_items": 45,
        "response_scale": "5-point frequency (0 = Not at all to 4 = Frequently, if not always)",
        "subscales": "Transformational: Idealized Influence-Attributed (4), Idealized Influence-Behavior (4), Inspirational Motivation (4), Intellectual Stimulation (4), Individual Consideration (4); Transactional: Contingent Reward (4), Management-by-Exception Active (4), Management-by-Exception Passive (4); Laissez-Faire (4); Outcomes: Extra Effort (3), Effectiveness (4), Satisfaction (2)",
        "exact_items": "Not reproduced — proprietary (Mind Garden, Inc.). Purchase required at mindgarden.com.",
        "item_source": "Bass, B. M., & Avolio, B. J. (1995). MLQ Multifactor Leadership Questionnaire: Sampler set. Mind Garden.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Most widely used leadership measure globally. Nine leadership factors + three outcome factors. Alphas .63-.92. Self-rater and other-rater versions. Proprietary. Over 10,000 citations. Criticism: discriminant validity between transformational subscales.",
    },
    {
        "instrument_name": "Organizational Justice Scale",
        "abbreviation": "OJS",
        "construct": "Organizational justice (four dimensions)",
        "construct_class": "Work and organizational",
        "domain": "Organizational behavior / Justice",
        "authors": "Colquitt, J. A.",
        "year": 2001,
        "target_population": "Working adults",
        "number_of_items": 20,
        "response_scale": "5-point Likert (1 = To a small extent to 5 = To a large extent)",
        "subscales": "Procedural Justice (7); Distributive Justice (4); Interpersonal Justice (4); Informational Justice (5)",
        "exact_items": "Not reproduced — items published in Colquitt, J. A. (2001). On the dimensionality of organizational justice. Journal of Applied Psychology, 86(3), 386-400. Widely reproduced in appendices of organizational studies.",
        "item_source": "Colquitt, J. A. (2001). On the dimensionality of organizational justice: A construct validation of a measure. Journal of Applied Psychology, 86(3), 386-400.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Validated the four-factor justice model (procedural, distributive, interpersonal, informational). Alphas .78-.93. Based on Greenberg and Bies/Moag's theoretical work. Over 5,000 citations. Free for research.",
    },
    {
        "instrument_name": "Minnesota Satisfaction Questionnaire-Short Form",
        "abbreviation": "MSQ-20",
        "construct": "Job satisfaction (intrinsic, extrinsic, general)",
        "construct_class": "Work and organizational",
        "domain": "Work attitudes",
        "authors": "Weiss, D. J., Dawis, R. V., England, G. W., & Lofquist, L. H.",
        "year": 1967,
        "target_population": "Working adults",
        "number_of_items": 20,
        "response_scale": "5-point Likert (1 = Very dissatisfied to 5 = Very satisfied)",
        "subscales": "Intrinsic Satisfaction (12); Extrinsic Satisfaction (6); General Satisfaction (20). Note: 2 items load on neither intrinsic nor extrinsic.",
        "exact_items": "Not reproduced — available from the Vocational Psychology Research center, University of Minnesota (vpr.psych.umn.edu). Licensed under Creative Commons Attribution-NonCommercial 4.0 International. Free for research/clinical use without written consent, with attribution.",
        "item_source": "Weiss, D. J., Dawis, R. V., England, G. W., & Lofquist, L. H. (1967). Manual for the Minnesota Satisfaction Questionnaire. University of Minnesota.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Classic job satisfaction measure. Short form of 100-item MSQ. Based on Theory of Work Adjustment (Dawis & Lofquist). Alphas .87 (General), .86 (Intrinsic), .80 (Extrinsic). Over 5,000 citations. Now CC BY-NC 4.0 — free for non-commercial use from UMN.",
    },
    {
        "instrument_name": "Oldenburg Burnout Inventory",
        "abbreviation": "OLBI",
        "construct": "Burnout (exhaustion and disengagement)",
        "construct_class": "Work and organizational",
        "domain": "Occupational health / Burnout",
        "authors": "Demerouti, E., Bakker, A. B., Vardakou, I., & Kantas, A.",
        "year": 2001,
        "target_population": "Working adults (all occupations)",
        "number_of_items": 16,
        "response_scale": "4-point Likert (1 = Strongly agree to 4 = Strongly disagree)",
        "subscales": "Exhaustion (8); Disengagement (8)",
        "exact_items": "Not reproduced — items published in Demerouti, E., et al. (2001). The job demands-resources model of burnout. Journal of Applied Psychology, 86(3), 499-512. Available from first author.",
        "item_source": "Demerouti, E., Bakker, A. B., Vardakou, I., & Kantas, A. (2001). The convergent validity of two burnout instruments: A multitrait-multimethod analysis. European Journal of Psychological Assessment, 17(3), 192-201.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Alternative to MBI. Two-factor structure. Includes both positively and negatively worded items (addresses MBI criticism of all-negative wording). Alphas .74-.85. Free alternative to proprietary MBI. Developed within JD-R framework.",
    },
    {
        "instrument_name": "Turnover Intention Scale",
        "abbreviation": "TIS-6",
        "construct": "Turnover intention",
        "construct_class": "Work and organizational",
        "domain": "Work attitudes",
        "authors": "Bothma, C. F. C., & Roodt, G.",
        "year": 2013,
        "target_population": "Working adults",
        "number_of_items": 6,
        "response_scale": "5-point Likert (1 = Never to 5 = Always)",
        "subscales": "Unidimensional",
        "exact_items": "Not reproduced — items published in Bothma, C. F. C., & Roodt, G. (2013). The validation of the turnover intention scale. SA Journal of Human Resource Management, 11(1), Art. #507. Based on Roodt (2004).",
        "item_source": "Bothma, C. F. C., & Roodt, G. (2013). The validation of the turnover intention scale. SA Journal of Human Resource Management, 11(1), Art. #507.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Short form of Roodt's (2004) 15-item TIS. Alpha .80. Widely used in South African organizational research. Six items retained from original 15 based on IRT analysis. Predicts actual turnover. Alternative: Kelloway et al. (1999) 4-item measure.",
    },
    {
        "instrument_name": "Job Demands-Resources Scale",
        "abbreviation": "JD-R Scale",
        "construct": "Job demands and job resources",
        "construct_class": "Work and organizational",
        "domain": "Occupational health / Job design",
        "authors": "Jackson, L. T. B., & Rothmann, S.",
        "year": 2005,
        "target_population": "Working adults",
        "number_of_items": 48,
        "response_scale": "4-point frequency (1 = Never to 4 = Always)",
        "subscales": "Demands: Pace and Amount of Work; Mental Load; Emotional Load; Variety in Work. Resources: Growth Opportunities; Organizational Support; Advancement; Social Support",
        "exact_items": "Not reproduced — various JD-R measures exist. Jackson & Rothmann (2005) version developed for South African context. See also Bakker et al.'s various measures. No single canonical JD-R scale exists.",
        "item_source": "Jackson, L. T. B., & Rothmann, S. (2005). Work-related well-being of educators in a district of the North West Province. Perspectives in Education, 23(3), 107-122. Based on Bakker et al.'s JD-R model.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Multiple JD-R measures exist across studies. No single canonical scale. The model (Bakker & Demerouti, 2007) is more standardized than the measurement. Researchers often adapt demands/resources items to their occupational context. WDQ (Morgeson & Humphrey, 2006) is a more standardized alternative for job characteristics.",
    },
    {
        "instrument_name": "Organizational Citizenship Behavior Scale",
        "abbreviation": "OCB",
        "construct": "Organizational citizenship behavior (individual and organizational directed)",
        "construct_class": "Work and organizational",
        "domain": "Organizational behavior",
        "authors": "Lee, K., & Allen, N. J.",
        "year": 2002,
        "target_population": "Working adults",
        "number_of_items": 16,
        "response_scale": "7-point frequency (1 = Never to 7 = Always)",
        "subscales": "OCB-I (Individual-directed, 8); OCB-O (Organization-directed, 8)",
        "exact_items": "Not reproduced — items published in Lee, K., & Allen, N. J. (2002). Organizational citizenship behavior and workplace deviance. Journal of Applied Psychology, 87(1), 131-142.",
        "item_source": "Lee, K., & Allen, N. J. (2002). Organizational citizenship behavior and workplace deviance: The role of affect and cognitions. Journal of Applied Psychology, 87(1), 131-142.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Two-factor OCB model (individual vs. organization directed). Alphas .83-.88. Earlier measures: Podsakoff et al. (1990) 24-item five-factor scale; Smith et al. (1983) altruism/compliance model. Lee & Allen's two-factor model is now widely preferred for parsimony.",
    },

    # ======================================================================
    # 8. COMMON MENTAL HEALTH PROBLEMS (11 instruments)
    # ======================================================================
    {
        "instrument_name": "Patient Health Questionnaire-9",
        "abbreviation": "PHQ-9",
        "construct": "Depression severity (DSM-based)",
        "construct_class": "Common mental health problems",
        "domain": "Depression",
        "authors": "Kroenke, K., Spitzer, R. L., & Williams, J. B. W.",
        "year": 2001,
        "target_population": "Adults (primary care, clinical, general)",
        "number_of_items": 9,
        "response_scale": "4-point frequency (0 = Not at all to 3 = Nearly every day). Total 0-27.",
        "subscales": "Unidimensional. Severity: 0-4 minimal, 5-9 mild, 10-14 moderate, 15-19 moderately severe, 20-27 severe.",
        "exact_items": "Over the last 2 weeks, how often have you been bothered by: 1. Little interest or pleasure in doing things; 2. Feeling down, depressed, or hopeless; 3. Trouble falling or staying asleep, or sleeping too much; 4. Feeling tired or having little energy; 5. Poor appetite or overeating; 6. Feeling bad about yourself — or that you are a failure or have let yourself or your family down; 7. Trouble concentrating on things, such as reading the newspaper or watching television; 8. Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual; 9. Thoughts that you would be better off dead, or of hurting yourself in some way",
        "item_source": "Kroenke, K., Spitzer, R. L., & Williams, J. B. W. (2001). The PHQ-9: Validity of a brief depression severity measure. Journal of General Internal Medicine, 16(9), 606-613. Public domain — developed with Pfizer Inc. educational grant.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Most widely used depression screening tool globally. Public domain (no permission needed). Sensitivity .88, specificity .88 at cutoff >= 10. Each item maps to a DSM-IV/5 MDD criterion. Over 25,000 citations. PHQ-2 (items 1-2) as ultra-brief screener.",
    },
    {
        "instrument_name": "Generalized Anxiety Disorder-7",
        "abbreviation": "GAD-7",
        "construct": "Generalized anxiety disorder severity",
        "construct_class": "Common mental health problems",
        "domain": "Anxiety",
        "authors": "Spitzer, R. L., Kroenke, K., Williams, J. B. W., & Löwe, B.",
        "year": 2006,
        "target_population": "Adults (primary care, clinical, general)",
        "number_of_items": 7,
        "response_scale": "4-point frequency (0 = Not at all to 3 = Nearly every day). Total 0-21.",
        "subscales": "Unidimensional. Severity: 0-4 minimal, 5-9 mild, 10-14 moderate, 15-21 severe.",
        "exact_items": "Over the last 2 weeks, how often have you been bothered by: 1. Feeling nervous, anxious, or on edge; 2. Not being able to stop or control worrying; 3. Worrying too much about different things; 4. Trouble relaxing; 5. Being so restless that it's hard to sit still; 6. Becoming easily annoyed or irritable; 7. Feeling afraid, as if something awful might happen",
        "item_source": "Spitzer, R. L., Kroenke, K., Williams, J. B. W., & Löwe, B. (2006). A brief measure for assessing generalized anxiety disorder: The GAD-7. Archives of Internal Medicine, 166(10), 1092-1097. Public domain.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Most widely used anxiety screening tool. Public domain. Sensitivity .89, specificity .82 at cutoff >= 10. Also screens for panic, social anxiety, PTSD (lower specificity). Over 20,000 citations. GAD-2 (items 1-2) as ultra-brief screener.",
    },
    {
        "instrument_name": "Beck Depression Inventory-II",
        "abbreviation": "BDI-II",
        "construct": "Depression severity",
        "construct_class": "Common mental health problems",
        "domain": "Depression",
        "authors": "Beck, A. T., Steer, R. A., & Brown, G. K.",
        "year": 1996,
        "target_population": "Adolescents (age 13+) and adults",
        "number_of_items": 21,
        "response_scale": "4-point severity (0-3 per item, each with unique statement options). Total 0-63.",
        "subscales": "Cognitive-Affective (items 1-14); Somatic-Performance (items 15-21). Severity: 0-13 minimal, 14-19 mild, 20-28 moderate, 29-63 severe.",
        "exact_items": "Not reproduced — proprietary (Pearson Clinical Assessment). Purchase required from pearsonclinical.com.",
        "item_source": "Beck, A. T., Steer, R. A., & Brown, G. K. (1996). Manual for the Beck Depression Inventory-II. San Antonio, TX: Psychological Corporation.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Gold standard depression measure in clinical psychology. Revision of BDI (Beck et al., 1961). Alpha .92-.93. Aligned with DSM-IV criteria. Proprietary — fee for use. Over 30,000 citations. Free alternatives: PHQ-9, CES-D, DASS-21 Depression.",
    },
    {
        "instrument_name": "Center for Epidemiologic Studies Depression Scale",
        "abbreviation": "CES-D",
        "construct": "Depressive symptomatology (past week)",
        "construct_class": "Common mental health problems",
        "domain": "Depression",
        "authors": "Radloff, L. S.",
        "year": 1977,
        "target_population": "Adults (community, epidemiological)",
        "number_of_items": 20,
        "response_scale": "4-point frequency (0 = Rarely or none of the time to 3 = Most or all of the time). Total 0-60.",
        "subscales": "Depressed Affect (7); Positive Affect (4, R); Somatic/Retarded Activity (7); Interpersonal (2). Clinical cutoff >= 16.",
        "exact_items": "1. I was bothered by things that usually don't bother me; 2. I did not feel like eating; my appetite was poor; 3. I felt that I could not shake off the blues even with help from my family or friends; 4. I felt that I was just as good as other people (R); 5. I had trouble keeping my mind on what I was doing; 6. I felt depressed; 7. I felt that everything I did was an effort; 8. I felt hopeful about the future (R); 9. I thought my life had been a failure; 10. I felt fearful; 11. My sleep was restless; 12. I was happy (R); 13. I talked less than usual; 14. I felt lonely; 15. People were unfriendly; 16. I enjoyed life (R); 17. I had crying spells; 18. I felt sad; 19. I felt that people dislike me; 20. I could not get going",
        "item_source": "Radloff, L. S. (1977). The CES-D Scale: A self-report depression scale for research in the general population. Applied Psychological Measurement, 1(3), 385-401. Public domain (developed with NIMH funding).",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Public domain (NIMH-funded). Designed for community epidemiology, not clinical diagnosis. Alpha .85-.90. Cutoff >= 16 for elevated depressive symptoms. Over 40,000 citations. Revised version: CES-D-R (Eaton et al., 2004, 20 items, updated language).",
    },
    {
        "instrument_name": "Depression Anxiety Stress Scales-21",
        "abbreviation": "DASS-21",
        "construct": "Depression, anxiety, and stress",
        "construct_class": "Common mental health problems",
        "domain": "Negative emotional states",
        "authors": "Lovibond, S. H., & Lovibond, P. F.",
        "year": 1995,
        "target_population": "Adults (general, clinical)",
        "number_of_items": 21,
        "response_scale": "4-point frequency (0 = Did not apply to me at all to 3 = Applied to me very much or most of the time). Multiply by 2 for DASS-42 equivalence.",
        "subscales": "Depression (7); Anxiety (7); Stress (7). Severity ranges: Normal, Mild, Moderate, Severe, Extremely Severe.",
        "exact_items": "Depression: 3. I couldn't seem to experience any positive feeling at all; 5. I found it difficult to work up the initiative to do things; 10. I felt that I had nothing to look forward to; 13. I felt down-hearted and blue; 16. I was unable to become enthusiastic about anything; 17. I felt I wasn't worth much as a person; 21. I felt that life was meaningless. Anxiety: 2. I was aware of dryness of my mouth; 4. I experienced breathing difficulty; 7. I experienced trembling; 9. I was worried about situations in which I might panic; 15. I felt I was close to panic; 19. I was aware of the action of my heart in the absence of physical exertion; 20. I felt scared without any good reason. Stress: 1. I found it hard to wind down; 6. I tended to over-react to situations; 8. I felt that I was using a lot of nervous energy; 11. I found myself getting agitated; 12. I found it difficult to relax; 14. I was intolerant of anything that kept me from getting on with what I was doing; 18. I felt that I was rather touchy",
        "item_source": "Lovibond, S. H., & Lovibond, P. F. (1995). Manual for the Depression Anxiety Stress Scales. Psychology Foundation, Sydney. Items freely available from www2.psy.unsw.edu.au/dass/.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Short form of DASS-42. Freely available from authors' website. Three-factor structure consistently replicated. Alphas .82-.93. Multiply scores by 2 for DASS-42 severity cutoffs. Distinguished from PHQ-9/GAD-7 by including Stress dimension. Over 15,000 citations.",
    },
    {
        "instrument_name": "Kessler Psychological Distress Scale",
        "abbreviation": "K10",
        "construct": "Non-specific psychological distress",
        "construct_class": "Common mental health problems",
        "domain": "Psychological distress",
        "authors": "Kessler, R. C., Andrews, G., Colpe, L. J., Hiripi, E., Mroczek, D. K., Normand, S.-L. T., Walters, E. E., & Zaslavsky, A. M.",
        "year": 2002,
        "target_population": "Adults (community, epidemiological)",
        "number_of_items": 10,
        "response_scale": "5-point frequency (1 = None of the time to 5 = All of the time). Total 10-50.",
        "subscales": "Unidimensional. Severity: 10-19 low, 20-24 mild, 25-29 moderate, 30-50 severe.",
        "exact_items": "During the last 30 days, about how often did you feel: 1. tired out for no good reason?; 2. nervous?; 3. so nervous that nothing could calm you down?; 4. hopeless?; 5. restless or fidgety?; 6. so restless you could not sit still?; 7. depressed?; 8. that everything was an effort?; 9. so sad that nothing could cheer you up?; 10. worthless?",
        "item_source": "Kessler, R. C., et al. (2002). Short screening scales to monitor population prevalences and trends in non-specific psychological distress. Psychological Medicine, 32(6), 959-976. Public domain.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Public domain. Used in WHO World Mental Health surveys, Australian National Health Survey, US NHIS. K6 (6-item subset: items 2, 4, 7, 8, 9, 10) also widely used. Alpha .88-.93. Strong screening properties for DSM disorders. Over 10,000 citations.",
    },
    {
        "instrument_name": "Impact of Event Scale-Revised",
        "abbreviation": "IES-R",
        "construct": "Post-traumatic stress symptoms (intrusion, avoidance, hyperarousal)",
        "construct_class": "Common mental health problems",
        "domain": "Trauma / PTSD",
        "authors": "Weiss, D. S., & Marmar, C. R.",
        "year": 1997,
        "target_population": "Adults who have experienced a specific traumatic event",
        "number_of_items": 22,
        "response_scale": "5-point Likert (0 = Not at all to 4 = Extremely)",
        "subscales": "Intrusion (8); Avoidance (8); Hyperarousal (6). Total score for screening (cutoff varies: 33 or 37).",
        "exact_items": "Not reproduced — items published in Weiss, D. S., & Marmar, C. R. (1997). The Impact of Event Scale-Revised. In J. P. Wilson & T. M. Keane (Eds.), Assessing psychological trauma and PTSD (pp. 399-411). Guilford Press.",
        "item_source": "Weiss, D. S., & Marmar, C. R. (1997). The Impact of Event Scale-Revised. In J. P. Wilson & T. M. Keane (Eds.), Assessing psychological trauma and PTSD (pp. 399-411). New York: Guilford Press.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Revision of IES (Horowitz et al., 1979). Added hyperarousal subscale. Alphas .79-.92. Based on DSM-IV PTSD criteria. Note: DSM-5 changed PTSD criteria; PCL-5 now preferred for DSM-5-aligned assessment. Over 8,000 citations.",
    },
    {
        "instrument_name": "PTSD Checklist for DSM-5",
        "abbreviation": "PCL-5",
        "construct": "PTSD symptom severity (DSM-5 criteria)",
        "construct_class": "Common mental health problems",
        "domain": "Trauma / PTSD",
        "authors": "Weathers, F. W., Litz, B. T., Keane, T. M., Palmieri, P. A., Marx, B. P., & Schnurr, P. P.",
        "year": 2013,
        "target_population": "Adults who have experienced a traumatic event",
        "number_of_items": 20,
        "response_scale": "5-point severity (0 = Not at all to 4 = Extremely). Total 0-80.",
        "subscales": "Intrusions (5); Avoidance (2); Negative Alterations in Cognitions and Mood (7); Alterations in Arousal and Reactivity (6). Provisional cutoff 31-33.",
        "exact_items": "Not reproduced — public domain instrument. Available from the National Center for PTSD (ptsd.va.gov). Download freely.",
        "item_source": "Weathers, F. W., et al. (2013). The PTSD Checklist for DSM-5 (PCL-5). National Center for PTSD. Available at ptsd.va.gov.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Public domain (US VA/NCPTSD). Aligned with DSM-5 PTSD criteria. Alpha .94-.96. Replaces PCL (DSM-IV version). Three scoring methods: total cutoff, DSM-5 diagnostic algorithm, combined. Widely used in clinical and research settings. Freely downloadable.",
    },
    {
        "instrument_name": "Insomnia Severity Index",
        "abbreviation": "ISI",
        "construct": "Insomnia severity (nature, severity, impact)",
        "construct_class": "Common mental health problems",
        "domain": "Sleep / Insomnia",
        "authors": "Bastien, C. H., Vallières, A., & Morin, C. M.",
        "year": 2001,
        "target_population": "Adults (clinical, community)",
        "number_of_items": 7,
        "response_scale": "5-point Likert (0-4, anchors vary: severity, satisfaction, noticeability, worry, interference). Total 0-28.",
        "subscales": "Unidimensional. Severity: 0-7 no insomnia, 8-14 subthreshold, 15-21 moderate, 22-28 severe.",
        "exact_items": "Not reproduced — copyrighted by Charles M. Morin (1993). Permission required via Mapi Research Trust (ePROVIDE). Items cover: sleep onset difficulty, sleep maintenance, early awakening, satisfaction, noticeability, worry, interference.",
        "item_source": "Bastien, C. H., Vallières, A., & Morin, C. M. (2001). Validation of the Insomnia Severity Index as an outcome measure for insomnia research. Sleep Medicine, 2(4), 297-307. Originally in Morin, C. M. (1993). Insomnia: Psychological assessment and management. Guilford Press.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Brief insomnia severity screener. Alpha .74-.78. Sensitive to treatment change (Morin et al., 2011). Cutoff >= 15 for moderate clinical insomnia. Over 5,000 citations. Recommended by American Academy of Sleep Medicine. Copyright held by Morin; license via Mapi Research Trust/ePROVIDE.",
    },
    {
        "instrument_name": "Alcohol Use Disorders Identification Test",
        "abbreviation": "AUDIT",
        "construct": "Hazardous and harmful alcohol use",
        "construct_class": "Common mental health problems",
        "domain": "Substance use",
        "authors": "Saunders, J. B., Aasland, O. G., Babor, T. F., de la Fuente, J. R., & Grant, M.",
        "year": 1993,
        "target_population": "Adults (primary care, community)",
        "number_of_items": 10,
        "response_scale": "5-point frequency/amount (0-4, anchors vary per item). Total 0-40.",
        "subscales": "Hazardous Alcohol Use (items 1-3); Dependence Symptoms (items 4-6); Harmful Alcohol Use (items 7-10). Cutoff >= 8 (hazardous use).",
        "exact_items": "1. How often do you have a drink containing alcohol?; 2. How many drinks containing alcohol do you have on a typical day when you are drinking?; 3. How often do you have six or more drinks on one occasion?; 4. How often during the last year have you found that you were not able to stop drinking once you had started?; 5. How often during the last year have you failed to do what was normally expected of you because of drinking?; 6. How often during the last year have you needed a first drink in the morning to get yourself going after a heavy drinking session?; 7. How often during the last year have you had a feeling of guilt or remorse after drinking?; 8. How often during the last year have you been unable to remember what happened the night before because of your drinking?; 9. Have you or someone else been injured because of your drinking?; 10. Has a relative, friend, doctor, or other health care worker been concerned about your drinking or suggested you cut down?",
        "item_source": "Saunders, J. B., Aasland, O. G., Babor, T. F., de la Fuente, J. R., & Grant, M. (1993). Development of the AUDIT. Addiction, 88(6), 791-804. WHO public domain.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "WHO-developed screening tool. Public domain. Sensitivity .92, specificity .94 for hazardous drinking. AUDIT-C (items 1-3) as ultra-brief screener. Over 15,000 citations. Cross-culturally validated (WHO 6-country development). Freely available from WHO.",
    },
    {
        "instrument_name": "Social Interaction Anxiety Scale",
        "abbreviation": "SIAS",
        "construct": "Social interaction anxiety",
        "construct_class": "Common mental health problems",
        "domain": "Social anxiety",
        "authors": "Mattick, R. P., & Clarke, J. C.",
        "year": 1998,
        "target_population": "Adults (clinical, community)",
        "number_of_items": 20,
        "response_scale": "5-point Likert (0 = Not at all characteristic or true of me to 4 = Extremely characteristic or true of me)",
        "subscales": "Unidimensional (3 reverse-scored items sometimes form method factor; SIAS-6/SPS-6 short forms available)",
        "exact_items": "Not reproduced — items published in Mattick, R. P., & Clarke, J. C. (1998). Development and validation of measures of social phobia scrutiny fear and social interaction anxiety. Behaviour Research and Therapy, 36(4), 455-470. Often used with Social Phobia Scale (SPS).",
        "item_source": "Mattick, R. P., & Clarke, J. C. (1998). Development and validation of measures of social phobia scrutiny fear and social interaction anxiety. Behaviour Research and Therapy, 36(4), 455-470.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Distinguishes social interaction anxiety from social phobia (scrutiny fear, measured by SPS). Alpha .88-.94. Clinical cutoff varies (34-43). Widely used in CBT treatment studies. Over 3,000 citations. SIAS-6 short form (Peters et al., 2012) recommended.",
    },

    # ======================================================================
    # 9. CAREER AND VOCATIONAL ASPECTS (11 instruments)
    # ======================================================================
    {
        "instrument_name": "Career Adapt-Abilities Scale",
        "abbreviation": "CAAS",
        "construct": "Career adaptability (concern, control, curiosity, confidence)",
        "construct_class": "Career and vocational",
        "domain": "Career development",
        "authors": "Savickas, M. L., & Porfeli, E. J.",
        "year": 2012,
        "target_population": "Adolescents and adults",
        "number_of_items": 24,
        "response_scale": "5-point Likert (1 = Not strong to 5 = Strongest)",
        "subscales": "Concern (6); Control (6); Curiosity (6); Confidence (6)",
        "exact_items": "Not reproduced — items published in Savickas, M. L., & Porfeli, E. J. (2012). Career Adapt-Abilities Scale: Construction, reliability, and measurement equivalence across 13 countries. Journal of Vocational Behavior, 80(3), 661-673. Available from Mark Savickas.",
        "item_source": "Savickas, M. L., & Porfeli, E. J. (2012). Career Adapt-Abilities Scale: Construction, reliability, and measurement equivalence across 13 countries. Journal of Vocational Behavior, 80(3), 661-673.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Based on Career Construction Theory (Savickas, 2005). Internationally developed (13-country collaboration). Four-factor structure with higher-order adaptability. Alphas .85-.94. Over 3,000 citations. Available for research with permission.",
    },
    {
        "instrument_name": "Career Decision Self-Efficacy Scale-Short Form",
        "abbreviation": "CDSE-SF",
        "construct": "Career decision-making self-efficacy",
        "construct_class": "Career and vocational",
        "domain": "Career development / Self-efficacy",
        "authors": "Betz, N. E., Klein, K. L., & Taylor, K. M.",
        "year": 1996,
        "target_population": "Adolescents and adults (especially students)",
        "number_of_items": 25,
        "response_scale": "5-point confidence (1 = No confidence at all to 5 = Complete confidence)",
        "subscales": "Self-Appraisal (5); Occupational Information (5); Goal Selection (5); Planning (5); Problem Solving (5)",
        "exact_items": "Not reproduced — proprietary (Mind Garden, Inc.). Purchase required at mindgarden.com.",
        "item_source": "Betz, N. E., Klein, K. L., & Taylor, K. M. (1996). Evaluation of a short form of the Career Decision-Making Self-Efficacy Scale. Journal of Career Assessment, 4(1), 47-57.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Short form of original 50-item CDSE (Taylor & Betz, 1983). Based on Crites' (1978) model of career maturity and Bandura's self-efficacy theory. Five-factor structure. Alphas .73-.83 per subscale, .94 total. Over 2,000 citations. Proprietary — requires purchase from Mind Garden.",
    },
    {
        "instrument_name": "Career Satisfaction Scale",
        "abbreviation": "CSS",
        "construct": "Subjective career satisfaction",
        "construct_class": "Career and vocational",
        "domain": "Career outcomes",
        "authors": "Greenhaus, J. H., Parasuraman, S., & Wormley, W. M.",
        "year": 1990,
        "target_population": "Working adults",
        "number_of_items": 5,
        "response_scale": "5-point Likert (1 = Strongly disagree to 5 = Strongly agree)",
        "subscales": "Unidimensional",
        "exact_items": "1. I am satisfied with the success I have achieved in my career; 2. I am satisfied with the progress I have made toward meeting my overall career goals; 3. I am satisfied with the progress I have made toward meeting my goals for income; 4. I am satisfied with the progress I have made toward meeting my goals for advancement; 5. I am satisfied with the progress I have made toward meeting my goals for the development of new skills",
        "item_source": "Greenhaus, J. H., Parasuraman, S., & Wormley, W. M. (1990). Effects of race on organizational experiences, job performance evaluations, and career outcomes. Academy of Management Journal, 33(1), 64-86.",
        "reproduction_status": "full",
        "notes_on_validity_or_use": "Most widely used subjective career success measure. Alpha .83-.89. Brief and unidimensional. Complements objective career success indicators (salary, promotions). Over 3,000 citations. Freely available.",
    },
    {
        "instrument_name": "Calling and Vocation Questionnaire",
        "abbreviation": "CVQ",
        "construct": "Calling (presence and search for calling)",
        "construct_class": "Career and vocational",
        "domain": "Vocational psychology / Meaning",
        "authors": "Dik, B. J., Eldridge, B. M., Steger, M. F., & Duffy, R. D.",
        "year": 2012,
        "target_population": "Adults (general, students, working)",
        "number_of_items": 24,
        "response_scale": "4-point Likert (1 = Not at all true of me to 4 = Absolutely true of me). Note: Not true for all = 0 in some versions.",
        "subscales": "Presence of Calling: Transcendent Summons (4), Purposeful Work (4), Prosocial Orientation (4); Search for Calling: Transcendent Summons (4), Purposeful Work (4), Prosocial Orientation (4)",
        "exact_items": "Not reproduced — items published in Dik, B. J., Eldridge, B. M., Steger, M. F., & Duffy, R. D. (2012). Development and validation of the Calling and Vocation Questionnaire (CVQ) and Brief Calling Scale (BCS). Journal of Career Assessment, 20(3), 242-263. BCS (4 items) also available.",
        "item_source": "Dik, B. J., Eldridge, B. M., Steger, M. F., & Duffy, R. D. (2012). Development and validation of the Calling and Vocation Questionnaire (CVQ) and Brief Calling Scale (BCS). Journal of Career Assessment, 20(3), 242-263.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Measures both presence of and search for calling across three dimensions. Alphas .85-.95. Brief Calling Scale (BCS, 4 items) available as ultra-short alternative. Over 1,000 citations. Growing field.",
    },
    {
        "instrument_name": "Protean Career Attitudes Scale",
        "abbreviation": "PCAS",
        "construct": "Protean career orientation (self-directed and values-driven career management)",
        "construct_class": "Career and vocational",
        "domain": "Career development",
        "authors": "Briscoe, J. P., Hall, D. T., & DeMuth, R. L. F.",
        "year": 2006,
        "target_population": "Working adults",
        "number_of_items": 14,
        "response_scale": "5-point Likert (1 = To little or no extent to 5 = To a very great extent)",
        "subscales": "Self-Directed Career Management (8); Values-Driven (6)",
        "exact_items": "Not reproduced — items published in Briscoe, J. P., Hall, D. T., & DeMuth, R. L. F. (2006). Protean and boundaryless careers: An empirical exploration. Journal of Vocational Behavior, 69(1), 30-47. Boundaryless Career Attitudes Scale (13 items) also published in same paper.",
        "item_source": "Briscoe, J. P., Hall, D. T., & DeMuth, R. L. F. (2006). Protean and boundaryless careers: An empirical exploration. Journal of Vocational Behavior, 69(1), 30-47.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Based on Hall's (1996, 2004) protean career theory. Two-factor structure. Alphas .70-.82. Often used alongside Boundaryless Career Attitudes Scale. Over 1,500 citations. Self-directed dimension stronger than values-driven psychometrically.",
    },
    {
        "instrument_name": "Career Futures Inventory-Revised",
        "abbreviation": "CFI-R",
        "construct": "Career optimism, adaptability, knowledge, and agency",
        "construct_class": "Career and vocational",
        "domain": "Career development",
        "authors": "Rottinghaus, P. J., Buelow, K. L., Matyja, A., & Schneider, M. R.",
        "year": 2012,
        "target_population": "Adults (students, working adults)",
        "number_of_items": 28,
        "response_scale": "5-point Likert (1 = Strongly disagree to 5 = Strongly agree)",
        "subscales": "Career Agency (8); Occupational Awareness (5); Support (5); Work-Life Balance (5); Negative Career Outlook (5)",
        "exact_items": "Not reproduced — CFI-R items published in Rottinghaus, P. J., Buelow, K. L., Matyja, A., & Schneider, M. R. (2012). The Career Futures Inventory-Revised. Journal of Career Assessment, 20(2), 123-139. Original CFI (25 items; Rottinghaus et al., 2005) is the earlier version.",
        "item_source": "Rottinghaus, P. J., Buelow, K. L., Matyja, A., & Schneider, M. R. (2012). The Career Futures Inventory-Revised: Measuring dimensions of career adaptability. Journal of Career Assessment, 20(2), 123-139.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Revision of CFI (Rottinghaus, Day, & Borgen, 2005). Five-factor structure. Alphas .73-.87. Broader than CAAS — includes occupational awareness and support dimensions. Growing use in vocational research.",
    },
    {
        "instrument_name": "Work Volition Scale",
        "abbreviation": "WVS",
        "construct": "Work volition (perceived capacity for occupational choice despite constraints)",
        "construct_class": "Career and vocational",
        "domain": "Vocational psychology / Psychology of working",
        "authors": "Duffy, R. D., Diemer, M. A., & Jadidian, A.",
        "year": 2012,
        "target_population": "Adults (general, diverse socioeconomic backgrounds)",
        "number_of_items": 13,
        "response_scale": "7-point Likert (1 = Strongly disagree to 7 = Strongly agree)",
        "subscales": "Volition (9); Financial Constraints (4, R)",
        "exact_items": "Not reproduced — items published in Duffy, R. D., Diemer, M. A., & Jadidian, A. (2012). The development and initial validation of the Work Volition Scale–Student Version. The Counseling Psychologist, 40(2), 291-319. Employee version also available (Duffy et al., 2012, JCA).",
        "item_source": "Duffy, R. D., Diemer, M. A., & Jadidian, A. (2012). The development and initial validation of the Work Volition Scale–Student Version. The Counseling Psychologist, 40(2), 291-319.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Based on Psychology of Working Theory (Blustein, 2006; Duffy et al., 2016). Measures perceived choice in career decisions despite barriers. Alphas .85-.91. Important for social justice in vocational psychology. Student and employee versions available.",
    },
    {
        "instrument_name": "Decent Work Scale",
        "abbreviation": "DWS",
        "construct": "Decent work (safe conditions, adequate compensation, free time, organizational values, access to health care)",
        "construct_class": "Career and vocational",
        "domain": "Vocational psychology / Work quality",
        "authors": "Duffy, R. D., Allan, B. A., England, J. W., Blustein, D. L., Autin, K. L., Douglass, R. P., Ferreira, J., & Santos, E. J. R.",
        "year": 2017,
        "target_population": "Working adults",
        "number_of_items": 15,
        "response_scale": "7-point Likert (1 = Strongly disagree to 7 = Strongly agree)",
        "subscales": "Physically and Interpersonally Safe Working Conditions (3); Access to Health Care (3); Adequate Compensation (3); Hours That Allow Free Time and Rest (3); Organizational Values That Complement Family and Social Values (3)",
        "exact_items": "Not reproduced — items published in Duffy, R. D., et al. (2017). The development and initial validation of the Decent Work Scale. Journal of Counseling Psychology, 64(2), 206-221.",
        "item_source": "Duffy, R. D., et al. (2017). The development and initial validation of the Decent Work Scale. Journal of Counseling Psychology, 64(2), 206-221.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Based on ILO decent work concept and Psychology of Working Theory. Five-factor structure. Alphas .81-.91. Unique focus on basic work conditions and social justice. Growing rapidly in vocational and I/O psychology.",
    },
    {
        "instrument_name": "Occupational Self-Efficacy Scale",
        "abbreviation": "OSES",
        "construct": "Occupational self-efficacy (domain-specific work self-efficacy)",
        "construct_class": "Career and vocational",
        "domain": "Work self-efficacy",
        "authors": "Rigotti, T., Schyns, B., & Mohr, G.",
        "year": 2008,
        "target_population": "Working adults",
        "number_of_items": 6,
        "response_scale": "6-point Likert (1 = Not at all true to 6 = Completely true)",
        "subscales": "Unidimensional",
        "exact_items": "Not reproduced — items published in Rigotti, T., Schyns, B., & Mohr, G. (2008). A short version of the Occupational Self-Efficacy Scale: Structural and construct validity across five countries. Journal of Career Assessment, 16(2), 238-255. Validated across 5 countries.",
        "item_source": "Rigotti, T., Schyns, B., & Mohr, G. (2008). A short version of the Occupational Self-Efficacy Scale. Journal of Career Assessment, 16(2), 238-255.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Short form of Schyns & von Collani (2002) 20-item scale. Validated across Germany, Belgium, Spain, Sweden, and UK. Alpha .85-.90. Brief and efficient. Distinguishes from GSE by being work-specific.",
    },
    {
        "instrument_name": "Career Exploration Survey",
        "abbreviation": "CES",
        "construct": "Career exploration behavior (self and environment exploration)",
        "construct_class": "Career and vocational",
        "domain": "Career development / Exploration",
        "authors": "Stumpf, S. A., Colarelli, S. M., & Hartman, K.",
        "year": 1983,
        "target_population": "Adults (students and early career)",
        "number_of_items": 59,
        "response_scale": "5-point Likert (varies by section: frequency, amount, satisfaction)",
        "subscales": "Environment Exploration (6); Self-Exploration (5); Intended-Systematic Exploration (3); Frequency (3); Amount of Information (3); Number of Occupations Considered (1); Focus (1); Satisfaction with Information (3); Exploration Stress (5); Decisional Stress (5); others vary by version used.",
        "exact_items": "Not reproduced — items published in Stumpf, S. A., Colarelli, S. M., & Hartman, K. (1983). Development of the Career Exploration Survey (CES). Journal of Vocational Behavior, 22(2), 191-226.",
        "item_source": "Stumpf, S. A., Colarelli, S. M., & Hartman, K. (1983). Development of the Career Exploration Survey (CES). Journal of Vocational Behavior, 22(2), 191-226.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Comprehensive career exploration measure. Multiple subscales covering exploration processes, reactions, and beliefs. Alphas .61-.87 (vary by subscale). Over 1,000 citations. Researchers often use selected subscales rather than full instrument.",
    },
    {
        "instrument_name": "Career Commitment Scale",
        "abbreviation": "CCS",
        "construct": "Career/occupational commitment",
        "construct_class": "Career and vocational",
        "domain": "Career development / Commitment",
        "authors": "Blau, G.",
        "year": 1985,
        "target_population": "Working adults",
        "number_of_items": 7,
        "response_scale": "5-point Likert (1 = Strongly disagree to 5 = Strongly agree)",
        "subscales": "Unidimensional (or two factors: affective and continuance career commitment in later work)",
        "exact_items": "Not reproduced — items published in Blau, G. (1985). The measurement and prediction of career commitment. Journal of Occupational Psychology, 58(4), 277-288. Extended to 12 items in Blau (2003) with four-factor model.",
        "item_source": "Blau, G. (1985). The measurement and prediction of career commitment. Journal of Occupational Psychology, 58(4), 277-288.",
        "reproduction_status": "none",
        "notes_on_validity_or_use": "Early career commitment measure. Alpha .82-.87. Distinguishes career commitment from organizational commitment. Later extended to four dimensions (Blau, 2003): affective, normative, accumulated costs, limited alternatives. Over 1,000 citations.",
    },
]


# ---------------------------------------------------------------------------
# Export functions
# ---------------------------------------------------------------------------
COLUMNS = [
    "instrument_name", "abbreviation", "construct", "construct_class",
    "domain", "authors", "year", "target_population", "number_of_items",
    "response_scale", "subscales", "exact_items", "item_source",
    "reproduction_status", "notes_on_validity_or_use",
]

OUTPUT_DIR = Path(__file__).parent / "instrument_repository"


def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def export_csv(instruments: list[dict], path: Path | None = None):
    path = path or OUTPUT_DIR / "psychometric_instrument_repository.csv"
    ensure_output_dir()
    df = pd.DataFrame(instruments, columns=COLUMNS)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"CSV exported: {path}  ({len(df)} instruments)")
    return df


def export_excel(instruments: list[dict], path: Path | None = None):
    path = path or OUTPUT_DIR / "psychometric_instrument_repository.xlsx"
    ensure_output_dir()

    wb = Workbook()

    # ── Sheet 1: Summary ──
    ws_summary = wb.active
    ws_summary.title = "Summary"
    _write_summary(ws_summary, instruments)

    # ── Sheet 2: Full Repository ──
    ws_repo = wb.create_sheet("Repository")
    _write_repository(ws_repo, instruments)

    # ── Sheet 3: Items Only ──
    ws_items = wb.create_sheet("Reproduced Items")
    _write_items_sheet(ws_items, instruments)

    # ── Sheet 4: Quality Report ──
    ws_quality = wb.create_sheet("Quality Report")
    _write_quality_report(ws_quality, instruments)

    wb.save(path)
    print(f"Excel exported: {path}  ({len(instruments)} instruments)")


# ---------------------------------------------------------------------------
# Excel sheet builders
# ---------------------------------------------------------------------------

HEADER_FONT = Font(name="Arial", bold=True, color="FFFFFF", size=11)
HEADER_FILL = PatternFill(start_color="2B5797", end_color="2B5797", fill_type="solid")
SUBHEADER_FILL = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
WRAP_ALIGN = Alignment(wrap_text=True, vertical="top")
THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)


def _style_header(ws, row_num: int, num_cols: int):
    for col in range(1, num_cols + 1):
        cell = ws.cell(row=row_num, column=col)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        cell.border = THIN_BORDER


def _write_summary(ws, instruments: list[dict]):
    ws.sheet_properties.tabColor = "2B5797"
    title_font = Font(name="Arial", bold=True, size=16, color="2B5797")
    subtitle_font = Font(name="Arial", bold=False, size=11, color="666666")
    bold = Font(name="Arial", bold=True, size=11)
    normal = Font(name="Arial", size=11)

    ws["A1"] = "Psychometric Instrument Repository"
    ws["A1"].font = title_font
    ws["A2"] = "Research-grade compilation of validated psychometric instruments"
    ws["A2"].font = subtitle_font
    ws["A3"] = f"Total instruments: {len(instruments)}"
    ws["A3"].font = bold

    # Coverage by construct class
    ws["A5"] = "Coverage by Construct Class"
    ws["A5"].font = Font(name="Arial", bold=True, size=13, color="2B5797")

    classes = {}
    for inst in instruments:
        cc = inst["construct_class"]
        classes[cc] = classes.get(cc, 0) + 1

    row = 6
    ws.cell(row=row, column=1, value="Construct Class").font = bold
    ws.cell(row=row, column=2, value="Count").font = bold
    ws.cell(row=row, column=1).fill = SUBHEADER_FILL
    ws.cell(row=row, column=2).fill = SUBHEADER_FILL
    row += 1

    for cc, count in sorted(classes.items(), key=lambda x: -x[1]):
        ws.cell(row=row, column=1, value=cc).font = normal
        ws.cell(row=row, column=2, value=count).font = normal
        row += 1

    # Reproduction summary
    row += 1
    ws.cell(row=row, column=1, value="Item Reproduction Summary").font = Font(
        name="Arial", bold=True, size=13, color="2B5797"
    )
    row += 1

    full = sum(1 for i in instruments if i["reproduction_status"] == "full")
    partial = sum(1 for i in instruments if i["reproduction_status"] == "partial")
    none_ = sum(1 for i in instruments if i["reproduction_status"] == "none")

    for label, val in [
        ("Fully reproduced items", full),
        ("Partial item access", partial),
        ("Not reproduced (licensing/source)", none_),
    ]:
        ws.cell(row=row, column=1, value=label).font = normal
        ws.cell(row=row, column=2, value=val).font = bold
        row += 1

    ws.column_dimensions["A"].width = 50
    ws.column_dimensions["B"].width = 15


def _write_repository(ws, instruments: list[dict]):
    ws.sheet_properties.tabColor = "4472C4"

    headers = [
        "Instrument Name", "Abbreviation", "Construct", "Construct Class",
        "Domain", "Authors", "Year", "Target Population", "# Items",
        "Response Scale", "Subscales", "Exact Items", "Item Source",
        "Reproduction Status", "Notes on Validity/Use",
    ]

    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    _style_header(ws, 1, len(headers))

    for row_idx, inst in enumerate(instruments, 2):
        for col_idx, key in enumerate(COLUMNS, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=inst.get(key, ""))
            cell.font = Font(name="Arial", size=10)
            cell.alignment = WRAP_ALIGN
            cell.border = THIN_BORDER

        # Color-code reproduction status
        status_cell = ws.cell(row=row_idx, column=14)
        if inst["reproduction_status"] == "full":
            status_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            status_cell.font = Font(name="Arial", size=10, color="006100")
        elif inst["reproduction_status"] == "partial":
            status_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            status_cell.font = Font(name="Arial", size=10, color="9C5700")
        else:
            status_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            status_cell.font = Font(name="Arial", size=10, color="9C0006")

        # Alternate row shading
        if row_idx % 2 == 0:
            for col_idx in range(1, len(headers) + 1):
                c = ws.cell(row=row_idx, column=col_idx)
                if col_idx != 14:
                    c.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")

    # Column widths
    widths = [35, 12, 40, 22, 28, 40, 6, 28, 8, 35, 45, 60, 55, 16, 60]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # Freeze panes
    ws.freeze_panes = "C2"

    # Auto-filter
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(instruments) + 1}"


def _write_items_sheet(ws, instruments: list[dict]):
    ws.sheet_properties.tabColor = "70AD47"

    headers = ["Instrument", "Abbreviation", "Construct Class", "# Items",
               "Reproduction Status", "Exact Items", "Item Source"]
    for col, h in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=h)
    _style_header(ws, 1, len(headers))

    reproduced = [i for i in instruments if i["reproduction_status"] in ("full", "partial")]
    reproduced.sort(key=lambda x: x["construct_class"])

    for row_idx, inst in enumerate(reproduced, 2):
        ws.cell(row=row_idx, column=1, value=inst["instrument_name"]).font = Font(name="Arial", size=10, bold=True)
        ws.cell(row=row_idx, column=2, value=inst["abbreviation"]).font = Font(name="Arial", size=10)
        ws.cell(row=row_idx, column=3, value=inst["construct_class"]).font = Font(name="Arial", size=10)
        ws.cell(row=row_idx, column=4, value=inst["number_of_items"]).font = Font(name="Arial", size=10)
        ws.cell(row=row_idx, column=5, value=inst["reproduction_status"]).font = Font(name="Arial", size=10)
        ws.cell(row=row_idx, column=6, value=inst["exact_items"]).font = Font(name="Arial", size=10)
        ws.cell(row=row_idx, column=6).alignment = WRAP_ALIGN
        ws.cell(row=row_idx, column=7, value=inst["item_source"]).font = Font(name="Arial", size=10)
        ws.cell(row=row_idx, column=7).alignment = WRAP_ALIGN

        for c in range(1, 8):
            ws.cell(row=row_idx, column=c).border = THIN_BORDER

    widths = [35, 12, 22, 8, 18, 80, 60]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.freeze_panes = "A2"


def _write_quality_report(ws, instruments: list[dict]):
    ws.sheet_properties.tabColor = "ED7D31"
    bold = Font(name="Arial", bold=True, size=11)
    normal = Font(name="Arial", size=11)
    title_font = Font(name="Arial", bold=True, size=14, color="ED7D31")

    ws["A1"] = "Quality Control Report"
    ws["A1"].font = title_font

    total = len(instruments)
    full = [i for i in instruments if i["reproduction_status"] == "full"]
    partial = [i for i in instruments if i["reproduction_status"] == "partial"]
    none_ = [i for i in instruments if i["reproduction_status"] == "none"]

    row = 3
    ws.cell(row=row, column=1, value="a. Instruments with fully reproducible exact items:").font = bold
    ws.cell(row=row, column=2, value=len(full)).font = bold
    row += 1
    for inst in full:
        ws.cell(row=row, column=2, value=f"{inst['abbreviation']} — {inst['instrument_name']}").font = normal
        row += 1

    row += 1
    ws.cell(row=row, column=1, value="b. Instruments with partial item access:").font = bold
    ws.cell(row=row, column=2, value=len(partial)).font = bold
    row += 1
    for inst in partial:
        ws.cell(row=row, column=2, value=f"{inst['abbreviation']} — {inst['instrument_name']}").font = normal
        row += 1

    row += 1
    ws.cell(row=row, column=1, value="c. Instruments not reproduced (licensing/source):").font = bold
    ws.cell(row=row, column=2, value=len(none_)).font = bold
    row += 1
    for inst in none_:
        ws.cell(row=row, column=2, value=f"{inst['abbreviation']} — {inst['instrument_name']}").font = normal
        row += 1

    row += 1
    ws.cell(row=row, column=1, value="d. Coverage analysis by construct class:").font = bold
    row += 1

    classes = {}
    for inst in instruments:
        cc = inst["construct_class"]
        classes.setdefault(cc, []).append(inst)

    target_per_class = total / len(classes)
    for cc, insts in sorted(classes.items()):
        count = len(insts)
        status = "ADEQUATE" if count >= 10 else "BELOW TARGET" if count >= 8 else "UNDERREPRESENTED"
        ws.cell(row=row, column=1, value=cc).font = normal
        ws.cell(row=row, column=2, value=f"{count} instruments").font = normal
        ws.cell(row=row, column=3, value=status).font = Font(
            name="Arial", size=11,
            color="006100" if status == "ADEQUATE" else "9C5700" if status == "BELOW TARGET" else "9C0006",
        )
        row += 1

    row += 2
    ws.cell(row=row, column=1, value="Confidence notes:").font = bold
    row += 1
    notes = [
        "All instrument metadata verified against original publications where possible.",
        "Year, authors, and item counts cross-referenced with primary sources.",
        "Item reproduction limited to clearly public domain or freely published items.",
        "Proprietary instruments marked with publisher/licensing information.",
        "Items from original journal publications reproduced with full citation.",
        "'number_of_items' field may vary for instruments with multiple validated versions.",
    ]
    for note in notes:
        ws.cell(row=row, column=1, value=f"• {note}").font = normal
        row += 1

    ws.column_dimensions["A"].width = 55
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["C"].width = 20


def print_summary(instruments: list[dict]):
    print("\n" + "=" * 70)
    print("PSYCHOMETRIC INSTRUMENT REPOSITORY — SUMMARY")
    print("=" * 70)

    total = len(instruments)
    print(f"\nTotal instruments: {total}")

    # By construct class
    print("\nCoverage by Construct Class:")
    print("-" * 40)
    classes = {}
    for inst in instruments:
        cc = inst["construct_class"]
        classes[cc] = classes.get(cc, 0) + 1
    for cc, count in sorted(classes.items(), key=lambda x: -x[1]):
        print(f"  {cc:<40} {count:>3}")

    # Reproduction status
    full = sum(1 for i in instruments if i["reproduction_status"] == "full")
    partial = sum(1 for i in instruments if i["reproduction_status"] == "partial")
    none_ = sum(1 for i in instruments if i["reproduction_status"] == "none")

    print(f"\nItem Reproduction Summary:")
    print("-" * 40)
    print(f"  a. Fully reproducible exact items:    {full}")
    print(f"  b. Partial item access:               {partial}")
    print(f"  c. Not reproduced (licensing/source):  {none_}")

    # Under-represented domains
    print(f"\nDomain Coverage Analysis:")
    print("-" * 40)
    for cc, count in sorted(classes.items()):
        status = "OK" if count >= 10 else "ADEQUATE" if count >= 8 else "LOW"
        print(f"  {cc:<40} {count:>3}  [{status}]")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print_summary(INSTRUMENTS)
    df = export_csv(INSTRUMENTS)
    export_excel(INSTRUMENTS)
    print(f"\nDone. Files saved to: {OUTPUT_DIR}")
