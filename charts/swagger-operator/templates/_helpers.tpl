{{/*
Expand the name of the chart.
*/}}
{{- define "swagger-admin.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "swagger-admin.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "swagger-admin.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "swagger-admin.labels" -}}
helm.sh/chart: {{ include "swagger-admin.chart" . }}
{{ include "swagger-admin.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "swagger-admin.selectorLabels" -}}
app.kubernetes.io/name: {{ include "swagger-admin.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "swagger-admin.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "swagger-admin.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the sso secret
*/}}
{{- define "swagger-admin.ssoSecretName" -}}
{{- if and .Values.sso.enabled .Values.sso.existingSecret }}
{{- default "default" .Values.sso.existingSecret }}
{{- else }}
{{- printf "%s-%s" (include "swagger-admin.fullname" .) "sso" }}
{{- end }}
{{- end }}