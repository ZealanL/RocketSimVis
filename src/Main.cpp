#include "VisInst/VisInst.h"

#include "../libsrc/cpp_sockets/src/simple_cpp_sockets.h"
#include "Serialization/Serialization.h"

#define PORT 9273

VisInst* visInst;

void ServerRecieveCallback(void* data, size_t size) {
	DataStreamIn inStream = DataStreamIn();
	inStream.data = std::vector<byte>((byte*)data, (byte*)data + size);

	visInst->updateMutex.lock();
	{
		try {
			Serialization::DeserializeUpdateArena(visInst->arenaInst, inStream);
			visInst->UpdateCarInfos();
			visInst->UpdateNewStates();
		} catch (std::exception& e) {
			RS_LOG("ServerRecieveCallback(): FAILED to deserialize:\n\t" << e.what());
		}
	}
	visInst->updateMutex.unlock();
}

void Server_Thread() {
	RS_LOG("Starting server thread...");
	UDPServer server = UDPServer(PORT);
	int bind_status = server.socket_bind();
	assert(!bind_status);
	server.listen(1024 * 1024, ServerRecieveCallback);
}

int main() {
	visInst = new VisInst();

	std::thread st = std::thread(Server_Thread);
	st.detach();

	visInst->Run();
}