# 🧠 ¿Cómo funciona este Proxy? (Arquitectura)

Este documento explica la "magia" detrás de escena que nos permite usar la herramienta paga **Claude Code** de forma totalmente gratuita aprovechando los servidores de NVIDIA NIM.

## 1. El Problema Base
**Claude Code** (la herramienta oficial de consola) está programada rígidamente para dos cosas:
1. Conectarse a los servidores oficiales de Anthropic.
2. Hablar el idioma (protocolo) exclusivo de Anthropic llamado *Messages API*.

Por otro lado, tenemos a **NVIDIA NIM**, que nos regala inferencia de modelos súper potentes (como Llama 3 o Minimax), pero sus servidores hablan el protocolo de **OpenAI**. 

Claude Code y NVIDIA no se entienden. Si conectamos uno directamente con el otro, la conexión fracasa porque hablan idiomas distintos.

## 2. La Solución: El Puente (LiteLLM)
Acá es donde entra nuestro script `main.py` impulsado por la librería **LiteLLM**. 
Levantamos un servidor que se pone exactamente en el medio de los dos y hace de **traductor simultáneo** en tiempo real. 

El flujo de información tiene 4 pasos clave:

### Paso 1: El Engaño (Secuestro de variables)
En vez de dejar que Claude Code se conecte a internet normalmente, le inyectamos dos variables de entorno en el archivo `run_claude.bat`:
```bat
set ANTHROPIC_BASE_URL=https://tu-proxy-en-render.onrender.com
set ANTHROPIC_API_KEY=tu-password-super-seguro
```
Con esto, Claude Code queda "ciego". Cree que está hablando con la empresa Anthropic, pero en realidad le está mandando todos los mensajes a nuestro servidor Proxy.

### Paso 2: Traducción de Protocolo (Anthropic ↔ OpenAI)
Cuando vos escribís un prompt, Claude Code lo empaqueta en un JSON con formato Anthropic y se lo manda al Proxy. 
LiteLLM agarra ese paquete, lo desarma, y lo **re-empaqueta en formato OpenAI** (que es el estándar de la industria). 

### Paso 3: Traducción de Modelos (El comodín `*`)
Claude Code le dice al proxy: *"Quiero que proceses esto usando el modelo `claude-3-5-sonnet-20241022`"*.
Pero NVIDIA no tiene a Claude, tiene a Minimax. 
Para resolver esto, usamos el archivo `litellm_config.yaml`. Ahí le metimos una regla comodín (`*`) que dice: 
> *"No importa qué nombre de modelo te pida Claude Code, decile que sí y mandale la tarea a `minimaxai/minimax-m3`"*.

### Paso 4: La Respuesta
1. El proxy le manda la petición (ya traducida y con el modelo cambiado) a los servidores de NVIDIA NIM usando tu `NVIDIA_API_KEY`.
2. NVIDIA procesa el mensaje y devuelve la respuesta en formato OpenAI.
3. El proxy agarra esa respuesta, la vuelve a traducir a formato Anthropic, y se la devuelve a Claude Code.
4. Claude Code la imprime en tu terminal creyendo que acaba de hablar con el verdadero Claude.

---

> [!TIP]
> **Por qué te responde "Soy Claude"**
> Cuando le preguntás al modelo quién es, te responde que es Claude a pesar de ser un modelo de Minimax. Esto pasa porque Claude Code inyecta automáticamente un *System Prompt* oculto en cada mensaje que dice algo como: *"Actuá como Claude, un asistente de Anthropic"*. El modelo de Minimax es tan obediente que lee esa instrucción y asume la personalidad a la perfección.
