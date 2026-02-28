# Agent Debate

This project facilitates a "debate" between multiple AI models to arrive at a more comprehensive and well-reasoned answer to a given prompt. The process involves generating initial responses, a critique phase, and a final synthesis.

## Current Progress

The core debate logic is implemented. The system can take a prompt, query multiple models, have them critique each other's responses, and then generate a final synthesized answer. The results of each run are logged in the `src/logs` directory.

## Debate Example

Here is a simple example of how the system works. The prompt was: "What are the best dietary choices for hypothyroidism?"

### Initial Claims

The initial responses from the models were analyzed to extract the core claims. The following table shows all the claims made by the models, and which models included them in their initial answers.

| Claim                                                                                                     | `google/gemini-1.5-flash-lite` | `anthropic/claude-3-haiku` | `openai/gpt-4o-mini` |
| --------------------------------------------------------------------------------------------------------- | :----------------------------: | :------------------------: | :------------------: |
| **Agreed Claims**                                                                                         |                                |                            |                      |
| A high-protein diet is beneficial.                                                                        |               ✅               |             ✅             |          ✅          |
| Selenium-rich foods are important.                                                                        |               ✅               |             ✅             |          ✅          |
| Cruciferous vegetables should be cooked.                                                                  |               ✅               |             ✅             |          ✅          |
| **Disagreed Claims**                                                                                      |                                |                            |                      |
| Iodine deficiency is a common cause of hypothyroidism.                                                    |                ❌                |             ✅             |          ❌          |
| Gluten should be considered for limitation/elimination, especially for those with autoimmune thyroid disease (Hashimoto's). |               ✅               |             ❌             |          ❌          |
| Iron is an essential nutrient to highlight for thyroid health due to common deficiency.                   |               ✅               |             ❌             |          ❌          |
| Vitamin D is an essential nutrient to highlight for thyroid health, particularly for autoimmune disease.  |               ✅               |             ❌             |          ❌          |
| B vitamins (especially B12) are essential nutrients to highlight for thyroid health due to common deficiency. |               ✅               |             ❌             |          ❌          |
| Probiotic-rich foods are beneficial for thyroid health.                                                   |               ✅               |             ❌             |          ❌          |
| Specific timing for thyroid medication is a critical dietary habit.                                       |               ✅               |             ❌             |          ❌          |
| Stress management, adequate sleep, and regular exercise are important lifestyle habits.                   |               ✅               |             ❌             |          ❌          |
| Excessive fiber supplements can interfere with medication absorption.                                     |               ✅               |             ❌             |          ❌          |
| Millet is a specific food (goitrogen) to avoid in excess.                                                 |                ❌                |             ❌             |          ✅          |

### The Value of Debate

As the table above shows, relying on a single model would have resulted in a less complete answer. For example:

*   A user of only **`anthropic/claude-3-haiku`** would have missed the importance of gluten, iron, vitamin D, B vitamins, probiotics, medication timing, lifestyle factors, and fiber supplements.
*   A user of only **`google/gemini-1.5-flash-lite`** would have missed that iodine deficiency is a common cause of hypothyroidism and that millet is a goitrogen to be avoided in excess.
*   A user of only **`openai/gpt-4o-mini`** would have missed the importance of gluten, iron, vitamin D, B vitamins, probiotics, medication timing, and lifestyle factors.

### Reaching Consensus

After a round of debate, where each model was shown the other models' responses, they reached a consensus on all the claims. This collaborative process ensures that the final answer is comprehensive and well-rounded.

### Final Synthesis

The final synthesized answer, which incorporates the collective knowledge of all the models, is shown below.

### The Gold Standard: Dietary Guidelines for Managing Hypothyroidism

Managing hypothyroidism effectively requires a combination of consistent medication and thoughtful dietary choices. While medication (typically levothyroxine) is the primary treatment, diet plays a crucial supporting role in optimizing thyroid function, managing symptoms, and improving overall well-being. The following guidelines synthesize the most evidence-based and practical recommendations.

#### Foundational Principle: Individualization
There is no universal "thyroid diet." Your approach should be personalized, especially if your hypothyroidism is caused by an autoimmune condition like Hashimoto's thyroiditis. Always consult your endocrinologist and a **registered dietitian (RD) specializing in thyroid health** before making significant changes.

---

#### 1. Prioritize These Essential Nutrients
Focus on obtaining key nutrients from whole foods to support thyroid hormone production and conversion.

*   **Iodine (Balance is Critical):** Essential for hormone synthesis. **Deficiency is a global cause of hypothyroidism, but excess can worsen autoimmune disease.**
    *   *Sources:* Iodized salt (used moderately), seafood, dairy, eggs.
    *   *Guidance:* Avoid high-dose supplements or excessive seaweed (like kelp) unless a deficiency is confirmed by your doctor.

*   **Selenium:** Vital for converting T4 (inactive) to T3 (active) hormone and protecting the thyroid gland.
    *   *Sources:* Brazil nuts (1-3 daily), tuna, sardines, eggs, chicken.

*   **Zinc:** Supports hormone production and the T4-to-T3 conversion.
    *   *Sources:* Oysters, red meat, poultry, pumpkin seeds, lentils.

*   **Iron:** Deficiency is common and can impair thyroid function.
    *   *Sources:* Red meat, lentils, spinach. **Pair with vitamin C** (e.g., bell peppers, citrus) to enhance absorption.

*   **Vitamin D:** Low levels are linked to autoimmune thyroid disease.
    *   *Sources:* Fatty fish (salmon, mackerel), fortified dairy, eggs. Sunlight exposure and supplementation (as advised by a doctor) are often necessary.

*   **Vitamin B12:** Deficiency is frequent and can mimic or worsen hypothyroid symptoms like fatigue.
    *   *Sources:* Meat, fish, eggs, dairy, fortified nutritional yeast.

---

#### 2. Build Your Diet on These Foods
*   **Whole, Unprocessed Foods:** The cornerstone of an anti-inflammatory, nutrient-dense diet.
*   **Lean Proteins:** Chicken, turkey, fish, legumes, and tofu support metabolism and satiety.
*   **Healthy Fats:** Omega-3s from fatty fish (salmon, mackerel), walnuts, chia seeds, and flaxseeds help reduce inflammation.
*   **Colorful Fruits and Vegetables:** Provide antioxidants. **Cook cruciferous vegetables** (broccoli, kale, Brussels sprouts) to significantly reduce their goitrogenic potential.
*   **Probiotic-Rich Foods:** Yogurt, kefir, sauerkraut, and kimchi support gut health, which is linked to immune and thyroid function.

---

#### 3. Be Mindful of These Foods & Substances
*   **Soy:** Contains isoflavones that may interfere with hormone production and medication absorption.
    *   *Guidance:* Consume in moderation and **at least 4 hours apart from your thyroid medication.**
*   **Gluten:** For those with Hashimoto's, gluten may trigger inflammation. A trial of a gluten-free diet may be beneficial, but undertake it with professional guidance.
*   **Goitrogens in Specific Foods:** Substances that can interfere with thyroid function.
    *   *Cruciferous Vegetables & Millet:* Enjoy them **cooked** and in normal culinary amounts. The goitrogenic effect is negligible for most people when prepared this way. Only massive, chronic intake of raw versions is a concern.
*   **Ultra-Processed Foods and Added Sugars:** Promote inflammation and weight gain, complicating symptom management.
*   **Excessive Alcohol and Caffeine:** Can disrupt hormone balance and sleep.

---

#### 4. Non-Negotiables: Medication & Lifestyle
*   **Medication Timing is Paramount:** Take levothyroxine on an empty stomach with water only, **at least 30-60 minutes before eating**, and **at least 4 hours apart from** calcium/iron supplements, antacids, and high-fiber meals.
*   **Manage Stress:** Chronic stress can negatively impact thyroid function. Incorporate practices like meditation, yoga, or walking.
*   **Prioritize Sleep & Movement:** Aim for 7-9 hours of quality sleep nightly. Regular, moderate exercise supports metabolism and energy levels.
*   **Stay Hydrated:** Essential for all metabolic processes.

### Final Synthesis
Effectively managing hypothyroidism with diet is about **strategic nourishment, not extreme restriction.** Build your meals around whole foods rich in selenium, zinc, iron, and vitamins D and B12. Consume iodine thoughtfully, cook goitrogenic vegetables, and space out potential interferents like soy and fiber from medication. Remember, the most perfect diet cannot replace medication, but a well-planned one, combined with proper medication adherence, and a healthy lifestyle, forms a powerful triad for optimal thyroid health and overall vitality. Always partner with your healthcare team to tailor this approach to your unique needs.
