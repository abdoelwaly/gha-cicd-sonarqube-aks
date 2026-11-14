{{- define "orders-api.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "orders-api.fullname" -}}
{{- printf "%s" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "orders-api.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Values.image.tag | default .Chart.AppVersion | quote }}
{{ include "orders-api.selectorLabels" . }}
{{- end -}}

{{- define "orders-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "orders-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
