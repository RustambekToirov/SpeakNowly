#!/usr/bin/env bash
set -euo pipefail

DB_URL="postgresql://backender:Fazliddin.000@localhost:5432/speaknowly"

for file in fixtures/*.json; do
    if [[ "$(basename "$file")" == "tariff_features.json" ]]; then
        continue
    fi
    table=$(basename "$file" .json)
    echo "→ Seeding (upsert) data into table: $table"

    jq -c '.[]' "$file" | while read -r row; do
        # === Step 1: Get list of columns ===
        readarray -t cols_array < <(echo "$row" | jq -r 'keys_unsorted[]')

        # === Step 2: Make comma-separated columns string ===
        cols=$(IFS=, ; echo "${cols_array[*]}")

        # === Step 3: Build VALUES with proper escaping ===
        vals=$(echo "$row" | jq -r '[.[]] |
            map(
                if . == null then
                    "NULL"
                elif type=="string" then
                    "'"'"'" + (gsub("'"'"'" ; "''")) + "'"'"'"
                else
                    tostring
                end
            ) | join(", ")')

        # === Step 4: Build ON CONFLICT clause ===
        update_parts=()
        for col in "${cols_array[@]}"; do
            if [[ "$col" != "id" ]]; then
                update_parts+=("$col = EXCLUDED.$col")
            fi
        done
        update_clause=$(IFS=, ; echo "${update_parts[*]}")

        # === Step 5: Execute SQL statement ===
        sql="
            INSERT INTO public.$table ($cols)
            VALUES ($vals)
            ON CONFLICT (id) DO UPDATE
            SET $update_clause;
        "
        psql "$DB_URL" -c "$sql"
    done
done

# 2. tariff_features.json в самом конце, если есть
TARIFF_FEATURES="fixtures/tariff_features.json"
if [[ -f "$TARIFF_FEATURES" ]]; then
    table="tariff_features"
    echo "→ Seeding (upsert) data into table: $table"
    jq -c '.[]' "$TARIFF_FEATURES" | while read -r row; do
        readarray -t cols_array < <(echo "$row" | jq -r 'keys_unsorted[]')
        cols=$(IFS=, ; echo "${cols_array[*]}")
        vals=$(echo "$row" | jq -r '[.[]] |
            map(
                if . == null then
                    "NULL"
                elif type=="string" then
                    "'"'"'" + (gsub("'"'"'" ; "''")) + "'"'"'"
                else
                    tostring
                end
            ) | join(", ")')
        update_parts=()
        for col in "${cols_array[@]}"; do
            if [[ "$col" != "id" ]]; then
                update_parts+=("$col = EXCLUDED.$col")
            fi
        done
        update_clause=$(IFS=, ; echo "${update_parts[*]}")
        sql="
            INSERT INTO public.$table ($cols)
            VALUES ($vals)
            ON CONFLICT (id) DO UPDATE
            SET $update_clause;
        "
        psql "$DB_URL" -c "$sql"
    done
fi

echo "✅ All fixtures applied (upsert)."