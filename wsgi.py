from ponydeck.ponydeck import ponydeck

def application(env, start_response):
  return ponydeck(env, start_response)
