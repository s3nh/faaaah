from schemas import AnalyticRecommendation, ResolutionAction
from pipeline import run_complaint_pipeline

complaint = """
I ordered a refrigerator 3 weeks ago and it still hasn't arrived.
I was charged immediately. Your support line keeps hanging up on me.
I want a refund AND compensation for the food I lost because I had no fridge.
If this isn't resolved by Friday I'm contacting my lawyer.
"""

historical_pairs = [
    {
        "complaint": "My order never arrived and I was charged.",
        "answer": "We apologize for the delay. We have initiated a full refund within 5-7 business days.",
    },
    {
        "complaint": "I want compensation for damages caused by a faulty product.",
        "answer": "Compensation claims for consequential damages require escalation to our resolution team.",
    },
    {
        "complaint": "Your support team is unresponsive.",
        "answer": "We sincerely apologize. A senior representative will contact you within 24 hours.",
    },
]

recommendation = AnalyticRecommendation(
    recommended_actions=[
        ResolutionAction(action_type="full_refund", value="100%", condition="order not delivered after 14 days"),
        ResolutionAction(action_type="escalation_to_senior_agent", condition="customer mentioned legal action"),
        ResolutionAction(action_type="goodwill_voucher", value="20 EUR", condition="VIP or first-time complaint"),
        ResolutionAction(action_type="consequential_damage_compensation", value="150 EUR", condition="verified food loss"),
    ],
    suggested_tone="empathetic and urgent",
    confidence_score=0.82,
)

result = run_complaint_pipeline(complaint, historical_pairs, recommendation)

print("\n" + "=" * 60)
print("FINAL PROPOSAL:")
print("=" * 60)
print(result["final_response"])
print(f"\nConfidence:           {result['confidence']:.0%}")
print(f"Approved actions:     {result['approved_actions']}")
print(f"Legal review needed:  {result['requires_legal_review']}")
print(f"Placeholders:         {result['placeholders']}")
