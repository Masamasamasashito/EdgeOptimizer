#!/bin/bash
# GCP Service Account権限チェックスクリプト
# EO_Documents/Manuals/py/CloudRun_README.mdに記載されている権限設定と実機の設定を比較します

set -e

# 環境変数設定
# すでに環境変数が設定されている場合はそれを使い、設定されていない場合はデフォルト値を使います
export EO_GCP_PROJECT_ID="${EO_GCP_PROJECT_ID:-eo-re-d01-pr-asne1}"
export EO_GCP_PROJECT_NUMBER="${EO_GCP_PROJECT_NUMBER:-<GCPプロジェクト番号>}"
export EO_GCP_CLOUD_RUN_SERVICE_NAME="${EO_GCP_CLOUD_RUN_SERVICE_NAME:-eo-re-d01-cloudrun-asne1}"
export EO_GCP_REGION="${EO_GCP_REGION:-asia-northeast1}"

# Service Account Email
export DEPLOY_SA="eo-gcp-sa-d01-deploy-asne1@${EO_GCP_PROJECT_ID}.iam.gserviceaccount.com"
export OAUTH2_INVOKER_SA="eo-gcp-sa-d01-oa2be-inv-asne1@${EO_GCP_PROJECT_ID}.iam.gserviceaccount.com"
export RUNTIME_SA="eo-gcp-sa-d01-runtime-asne1@${EO_GCP_PROJECT_ID}.iam.gserviceaccount.com"
export COMPUTE_DEFAULT_SA="${EO_GCP_PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "=========================================="
echo "GCP Service Account 権限チェック"
echo "=========================================="
echo "プロジェクトID: ${EO_GCP_PROJECT_ID}"
echo "プロジェクト番号: ${EO_GCP_PROJECT_NUMBER}"
echo ""

# 期待される権限定義
declare -A EXPECTED_DEPLOY_PROJECT_ROLES=(
    ["roles/run.admin"]="Cloud Run 管理者"
    ["roles/cloudbuild.builds.editor"]="Cloud Build 編集者"
    ["roles/serviceusage.serviceUsageConsumer"]="Service Usage ユーザー"
    ["roles/storage.admin"]="ストレージ管理者"
    ["roles/artifactregistry.admin"]="Artifact Registry 管理者"
)

declare -A EXPECTED_RUNTIME_PROJECT_ROLES=(
    ["roles/secretmanager.secretAccessor"]="Secret Manager のシークレット アクセサー"
)

# 関数: プロジェクトレベルロールの確認
check_project_level_roles() {
    local SA_EMAIL=$1
    local SA_NAME=$2
    local -n EXPECTED_ROLES=$3
    
    echo "----------------------------------------"
    echo "[${SA_NAME}] プロジェクトレベルロール確認"
    echo "----------------------------------------"
    echo "Service Account: ${SA_EMAIL}"
    echo ""
    
    # 実際のロールを取得
    ACTUAL_ROLES=$(gcloud projects get-iam-policy ${EO_GCP_PROJECT_ID} \
        --flatten="bindings[].members" \
        --filter="bindings.members:serviceAccount:${SA_EMAIL}" \
        --format="value(bindings.role)" 2>/dev/null || echo "")
    
    if [ -z "$ACTUAL_ROLES" ]; then
        echo "❌ エラー: プロジェクトレベルロールが見つかりません"
        echo ""
        return 1
    fi
    
    echo "実際に設定されているロール:"
    echo "$ACTUAL_ROLES" | while read -r role; do
        if [ -n "$role" ]; then
            echo "  ✓ $role"
        fi
    done
    echo ""
    
    # 期待されるロールとの比較
    echo "期待されるロールとの比較:"
    local MISSING_ROLES=()
    for role in "${!EXPECTED_ROLES[@]}"; do
        if echo "$ACTUAL_ROLES" | grep -q "^${role}$"; then
            echo "  ✓ $role (${EXPECTED_ROLES[$role]})"
        else
            echo "  ❌ $role (${EXPECTED_ROLES[$role]}) - 見つかりません"
            MISSING_ROLES+=("$role")
        fi
    done
    echo ""
    
    # 予期しないロールの確認
    echo "予期しないロール（ドキュメントに記載されていない）:"
    local UNEXPECTED_FOUND=false
    echo "$ACTUAL_ROLES" | while read -r role; do
        if [ -n "$role" ] && [ -z "${EXPECTED_ROLES[$role]}" ]; then
            echo "  ⚠ $role - ドキュメントに記載されていません"
            UNEXPECTED_FOUND=true
        fi
    done
    if [ "$UNEXPECTED_FOUND" = false ]; then
        echo "  (なし)"
    fi
    echo ""
    
    if [ ${#MISSING_ROLES[@]} -gt 0 ]; then
        echo "❌ 不足しているロール: ${MISSING_ROLES[*]}"
        echo ""
        return 1
    else
        echo "✓ すべての期待されるロールが設定されています"
        echo ""
        return 0
    fi
}

# 関数: リソースレベルロールの確認
check_resource_level_roles() {
    local SA_EMAIL=$1
    local SA_NAME=$2
    local EXPECTED_PRINCIPALS=$3
    
    echo "----------------------------------------"
    echo "[${SA_NAME}] リソースレベルロール確認"
    echo "----------------------------------------"
    echo "Service Account: ${SA_EMAIL}"
    echo ""
    
    # 実際のIAMポリシーを取得
    IAM_POLICY=$(gcloud iam service-accounts get-iam-policy ${SA_EMAIL} \
        --project=${EO_GCP_PROJECT_ID} \
        --format="json" 2>/dev/null || echo "{}")
    
    if [ "$IAM_POLICY" = "{}" ]; then
        echo "❌ エラー: IAMポリシーを取得できませんでした"
        echo ""
        return 1
    fi
    
    echo "実際に設定されている権限:"
    echo "$IAM_POLICY" | grep -A 5 "bindings" || echo "  (権限が設定されていません)"
    echo ""
    
    # 期待されるプリンシパルの確認
    echo "期待されるプリンシパルとの比較:"
    # この部分は手動で確認が必要です
    echo "  (gcloud iam service-accounts get-iam-policy の出力を確認してください)"
    echo ""
}

# 関数: Cloud RunサービスへのInvokerロール確認
check_cloudrun_invoker_role() {
    echo "----------------------------------------"
    echo "[OAuth2_Invoker SA] Cloud Run Invokerロール確認"
    echo "----------------------------------------"
    echo "Service Account: ${OAUTH2_INVOKER_SA}"
    echo "Cloud Run Service: ${EO_GCP_CLOUD_RUN_SERVICE_NAME}"
    echo ""
    
    # Cloud RunサービスのIAMポリシーを取得
    IAM_POLICY=$(gcloud run services get-iam-policy ${EO_GCP_CLOUD_RUN_SERVICE_NAME} \
        --region=${EO_GCP_REGION} \
        --project=${EO_GCP_PROJECT_ID} \
        --format="json" 2>/dev/null || echo "{}")
    
    if [ "$IAM_POLICY" = "{}" ]; then
        echo "❌ エラー: Cloud RunサービスのIAMポリシーを取得できませんでした"
        echo ""
        return 1
    fi
    
    # roles/run.invokerが設定されているか確認
    if echo "$IAM_POLICY" | grep -q "${OAUTH2_INVOKER_SA}"; then
        if echo "$IAM_POLICY" | grep -q "roles/run.invoker"; then
            echo "✓ roles/run.invoker が設定されています"
        else
            echo "⚠ ${OAUTH2_INVOKER_SA} は見つかりましたが、roles/run.invoker が設定されていません"
        fi
    else
        echo "❌ ${OAUTH2_INVOKER_SA} に roles/run.invoker が設定されていません"
        echo ""
        echo "設定コマンド:"
        echo "gcloud run services add-iam-policy-binding ${EO_GCP_CLOUD_RUN_SERVICE_NAME} \\"
        echo "  --region=${EO_GCP_REGION} \\"
        echo "  --member=\"serviceAccount:${OAUTH2_INVOKER_SA}\" \\"
        echo "  --role=\"roles/run.invoker\" \\"
        echo "  --project=${EO_GCP_PROJECT_ID}"
        echo ""
        return 1
    fi
    echo ""
}

# メイン処理
echo "1. Deployer SA のプロジェクトレベルロール確認"
check_project_level_roles "${DEPLOY_SA}" "Deployer SA" EXPECTED_DEPLOY_PROJECT_ROLES
DEPLOY_PROJECT_RESULT=$?

echo "2. Runtime SA のプロジェクトレベルロール確認"
check_project_level_roles "${RUNTIME_SA}" "Runtime SA" EXPECTED_RUNTIME_PROJECT_ROLES
RUNTIME_PROJECT_RESULT=$?

echo "3. Deployer SA のリソースレベルロール確認"
check_resource_level_roles "${DEPLOY_SA}" "Deployer SA" "WIFプリンシパル"
echo "期待される設定:"
echo "  - roles/iam.workloadIdentityUser"
echo "  - プリンシパル: principalSet://iam.googleapis.com/projects/${EO_GCP_PROJECT_NUMBER}/locations/global/workloadIdentityPools/eo-gcp-pool-wif-d01/attribute.repository/Masamasamasashito/multi-cloud-request-engine-test"
echo ""

echo "4. Compute Engine デフォルト SA のリソースレベルロール確認"
check_resource_level_roles "${COMPUTE_DEFAULT_SA}" "Compute Engine デフォルト SA (Build Executor)" "Deployer SA"
echo "期待される設定:"
echo "  - roles/iam.serviceAccountUser"
echo "  - プリンシパル: serviceAccount:${DEPLOY_SA}"
echo "  (※最新のGCPプロジェクトでは、ビルド実行のためにDeployerがこのSAを借用する必要があります)"
echo ""

echo "5. OAuth2_Invoker SA のリソースレベルロール確認"
check_resource_level_roles "${OAUTH2_INVOKER_SA}" "OAuth2_Invoker SA" "自分自身"
echo "期待される設定:"
echo "  - roles/iam.serviceAccountTokenCreator"
echo "  - プリンシパル: serviceAccount:${OAUTH2_INVOKER_SA}"
echo ""

echo "6. Runtime SA のリソースレベルロール確認"
check_resource_level_roles "${RUNTIME_SA}" "Runtime SA" "Build Executors & Deployer SA"
echo "期待される設定:"
echo "  - roles/iam.serviceAccountUser"
echo "  - プリンシパル1: serviceAccount:${EO_GCP_PROJECT_NUMBER}@cloudbuild.gserviceaccount.com (レガシー版ビルド実行者)"
echo "  - プリンシパル2: serviceAccount:${COMPUTE_DEFAULT_SA} (最新版ビルド実行者)"
echo "  - プリンシパル3: serviceAccount:${DEPLOY_SA} (直デプロイ時)"
echo ""

echo "7. OAuth2_Invoker SA の Cloud Run Invokerロール確認"
check_cloudrun_invoker_role
CLOUDRUN_INVOKER_RESULT=$?

echo "=========================================="
echo "チェック結果サマリー"
echo "=========================================="
if [ $DEPLOY_PROJECT_RESULT -eq 0 ] && [ $RUNTIME_PROJECT_RESULT -eq 0 ] && [ $CLOUDRUN_INVOKER_RESULT -eq 0 ]; then
    echo "✓ すべての主要な権限が正しく設定されています"
    exit 0
else
    echo "❌ 一部の権限に問題があります。上記の詳細を確認してください"
    exit 1
fi

