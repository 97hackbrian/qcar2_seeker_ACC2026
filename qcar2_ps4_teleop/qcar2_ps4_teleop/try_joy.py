import pygame

# Inicializa pygame y el mando
pygame.init()
pygame.joystick.init()


def main():
	if pygame.joystick.get_count() == 0:
	    print("No hay mandos conectados.")
	else:
	    joystick = pygame.joystick.Joystick(0)
	    joystick.init()
	    print(f"Mando detectado: {joystick.get_name()}")

	    # Bucle para probar botones y eventos
	    try:
	        while True:
	            pygame.event.pump()
	            for i in range(joystick.get_numbuttons()):
	                if joystick.get_button(i):
	                    print(f"Botón presionado: {i}")
	            for i in range(joystick.get_numaxes()):
	                axis_value = joystick.get_axis(i)
	                if abs(axis_value) > 0.1:  # Umbral para evitar ruido
	                    print(f"Eje {i} valor: {axis_value}")
	    except KeyboardInterrupt:
	        print("Finalizando prueba.")
	    finally:
	        pygame.quit()

if __name__ == '__main__':
    main()
