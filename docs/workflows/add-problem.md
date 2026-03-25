# /project:add-problem

Scaffold a new problem for the Docker Playground problem bank.

Steps:
1. Ask the user: problem title, difficulty (easy/medium/hard), app type (nginx/node/python/etc), port number, health endpoint path
2. Determine the next available problem number by listing problems/ directory
3. Create the folder structure:
   - problems/NN-slug/problem.json
   - problems/NN-slug/README.md (with problem statement template)
   - problems/NN-slug/app/ (with minimal working app code)
   - problems/NN-slug/test.sh (with curl health check)
   - problems/NN-slug/solution/Dockerfile (reference solution)
4. Use a subagent to validate the problem: "Use the problem-validator subagent to validate problems/NN-slug"
5. Report the result
