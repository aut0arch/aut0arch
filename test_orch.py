import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "server"))
import orchestrator

# Just run with the local tests folder that contains Java files
print("Running orchestrator test...")
orchestrator.run_pipeline("file:///home/n1ved/Documents/aut0arch/parser/tests")
print("Done!")
