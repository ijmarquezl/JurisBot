# Metodología SecWeb 2.0: Framework para Agentes de Desarrollo
**Estado:** Modernización de SecWeb (2007) | **Enfoque:** Agentes Autónomos + Seguridad LLM

## 1. El Cambio de Paradigma
SecWeb 2.0 sustituye el desarrollo manual por **Ciclos de Inferencia y Auditoría**. La seguridad ya no es una fase final, sino una restricción de diseño embebida en los Meta-Prompts.

## 2. Fases de la Metodología
1.  **Análisis y Definición (Requirement Analysis):**
    *   **Input:** Interacción Agente-Analista/Usuario.
    *   **Output:** Definición del Stack Tecnológico (Lenguaje, DB, Framework), Estructura del Proyecto y Requerimientos Validados.
2.  **Orquestación:** Configuración del entorno y selección de roles de IA específicos para el stack definido.
3.  **Diseño Generativo:** Creación de diagramas y documentación de Prompts (el nuevo diseño físico).
4.  **Inferencia Segura:** Generación de código mediante roles con Guardrails.
5.  **Auditoría de Inyección:** Red Teaming específico para prompts y OWASP.
6.  **Validación Humana (Gatekeeping):** Aprobación del ciclo para despliegue.

## 3. Estándares Universales (Polyglot)
Independientemente del lenguaje seleccionado en la fase de Análisis, todo código debe cumplir:
*   **Clean Architecture:** Separación estricta de Capas (Dominio, Aplicación, Infraestructura).
*   **Principios SOLID y DRY:** Código modular, mantenible y sin duplicidad.
*   **Convention over Configuration:** Uso de estándares de industria para estructura de carpetas.
*   **English-based Naming:** Código autodocumentado en inglés.
*   **Semantic Commits:** Historial de cambios legible y estructurado.

## 4. Métricas de Éxito
*   **D.F.I (Densidad de Fallos por Inferencia):** Intentos fallidos del agente antes del código estable.
*   **P.I.R (Prompt Injection Resilience):** Capacidad del código/prompt para resistir ataques de manipulación.
