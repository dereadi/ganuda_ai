# Enhanced FARA vision integration - replaces /look command
async def fara_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """FARA capabilities: /fara <action> [args]

    Actions:
      look [question] - Analyze sasass screen
      quiz <topic> - Generate quiz questions
      remember <query> - Search FARA's memories
    """
    args = context.args
    if not args:
        await update.message.reply_text(
            "FARA Commands:\n"
            "/fara look [question] - What's on sasass screen?\n"
            "/fara quiz <topic> - Generate quiz\n"
            "/fara screenshot - Take sasass screenshot"
        )
        return

    action = args[0].lower()

    if action == "look":
        question = " ".join(args[1:]) if len(args) > 1 else "What do you see?"
        await do_fara_look(update, question)
    elif action == "quiz":
        topic = " ".join(args[1:]) if len(args) > 1 else "general knowledge"
        await do_fara_quiz(update, topic)
    elif action == "screenshot":
        await do_fara_screenshot(update)
    else:
        await update.message.reply_text(f"Unknown FARA action: {action}")


async def do_fara_look(update: Update, question: str):
    """Execute FARA look on sasass"""
    thinking_msg = await update.message.reply_text("FARA is looking... (~30 sec)")

    safe_question = question.replace("'", "'\"'\"'")
    cmd = f"ssh dereadi@192.168.132.241 \"python3 /Users/Shared/ganuda/scripts/fara_look.py '{safe_question}'\""

    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

        output = stdout.decode()
        if "FARA Response:" in output:
            response = output.split("FARA Response:")[-1].strip()
            response = response.replace("=" * 60, "").strip()
            await thinking_msg.edit_text(f"FARA sees:\n\n{response[:3500]}")
        else:
            await thinking_msg.edit_text(f"FARA: {output[-1500:]}")

    except asyncio.TimeoutError:
        await thinking_msg.edit_text("FARA timed out - model loading takes ~30 seconds")
    except Exception as e:
        await thinking_msg.edit_text(f"FARA error: {str(e)}")


async def do_fara_screenshot(update: Update):
    """Take and send sasass screenshot"""
    thinking_msg = await update.message.reply_text("Capturing sasass screen...")

    try:
        # Capture screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        remote_path = f"/tmp/fara_screenshot_{timestamp}.png"
        local_path = f"/tmp/fara_screenshot_{timestamp}.png"

        # Take screenshot on sasass
        await asyncio.create_subprocess_shell(
            f"ssh dereadi@192.168.132.241 'screencapture -x {remote_path}'"
        )
        await asyncio.sleep(1)

        # Copy to local
        await asyncio.create_subprocess_shell(
            f"scp dereadi@192.168.132.241:{remote_path} {local_path}"
        )
        await asyncio.sleep(1)

        # Send photo
        with open(local_path, 'rb') as photo:
            await update.message.reply_photo(photo, caption="sasass screen capture")

        await thinking_msg.delete()

    except Exception as e:
        await thinking_msg.edit_text(f"Screenshot error: {e}")