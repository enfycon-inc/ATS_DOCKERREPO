docker exec ats_postgres psql -U ats_user -d ats_db -c "SELECT branch_id, assigned_branch_ids FROM ats.users WHERE email='sahadeb@enfycon.com';"
