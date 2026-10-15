{{- define "washq.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "washq.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "washq.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "washq.labels" -}}
app.kubernetes.io/name: {{ include "washq.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}

{{- define "washq.backendSelector" -}}
app.kubernetes.io/name: {{ include "washq.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: backend
{{- end -}}

{{- define "washq.frontendSelector" -}}
app.kubernetes.io/name: {{ include "washq.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: frontend
{{- end -}}

{{- define "washq.postgresSelector" -}}
app.kubernetes.io/name: {{ include "washq.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: postgres
{{- end -}}

{{/*
Image reference. The registry is optional so a locally built image can be
used on kind, where there is no registry to pull from.
*/}}
{{- define "washq.image" -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion -}}
{{- if .Values.image.registry -}}
{{ .Values.image.registry }}/{{ .Values.image.repository }}/{{ .component }}:{{ $tag }}
{{- else -}}
{{ .Values.image.repository }}-{{ .component }}:{{ $tag }}
{{- end -}}
{{- end -}}

{{- define "washq.postgresSecretName" -}}
{{- if .Values.postgres.existingSecret -}}
{{ .Values.postgres.existingSecret }}
{{- else -}}
{{ include "washq.fullname" . }}-postgres
{{- end -}}
{{- end -}}

{{/*
Postgres service name. Defined once so the Deployment and the migration
job cannot drift apart.
*/}}
{{- define "washq.databaseHost" -}}
{{ include "washq.fullname" . }}-postgres
{{- end -}}

{{/*
Environment shared by the backend container and the migration init
container, so they always point at the same database.
*/}}
{{- define "washq.backendEnv" -}}
- name: POSTGRES_USER
  valueFrom:
    secretKeyRef:
      name: {{ include "washq.postgresSecretName" . }}
      key: POSTGRES_USER
- name: POSTGRES_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "washq.postgresSecretName" . }}
      key: POSTGRES_PASSWORD
- name: POSTGRES_DB
  valueFrom:
    secretKeyRef:
      name: {{ include "washq.postgresSecretName" . }}
      key: POSTGRES_DB
- name: DATABASE_URL
  value: "postgresql+psycopg://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@{{ include "washq.databaseHost" . }}:5432/$(POSTGRES_DB)"
- name: SLOT_MINUTES
  value: {{ .Values.backend.env.slotMinutes | quote }}
- name: HOSTEL_TZ
  value: {{ .Values.backend.env.hostelTz | quote }}
- name: APP_VERSION
  value: {{ .Values.image.tag | default .Chart.AppVersion | quote }}
{{- end -}}
