# T4 readiness diagnostic block — 11 November 2026

Observed start17:20:50 Asia/Calcutta. User approves bounded10-second worker deadline; all other limits unchanged. Recovery from10November handoff: direct database URL saved and manualdeploy done, health/demo200 but ready503 measured3.411s. No secrets or private resource metadata copied into repository.

Production deadline regression changed from<=3 to exact10 under explicit approval, redassert3==10. Implementation changes constant only; worker docstring follows. Fullrun found cleanup test timing expectedoldproductiondeadline. Preserved original<6s and actualPID/reaping checks by injecting3s in that one test; separateproductiondeadline test remains10. Full479Python pass20.46s with existingStarlettewarning, Ruff/assumptionsgreen. No frozen T1/T2/T3 test changed. Push/CI/deploy/live measurements follow. Activeeffort excludes waits; endtimestamp at handoff.
