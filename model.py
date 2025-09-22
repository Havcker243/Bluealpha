# import pickle
# import sys 
# import meridian

# # Load the model
# sys.modules["meridian.model"] = meridian
# with open("saved_mmm.pkl", "rb") as f:
#     model = pickle.load(f)

# # Run predictions ("what-if" scenarios)
# new_data = {
#     "tv": 100000,
#     "digital": 50000,
#     "social": 20000
# }
# results = model.predict(new_data)

# # Export to JSON
# import json
# with open("results.json", "w") as f:
#     json.dump(results, f, indent=2)
