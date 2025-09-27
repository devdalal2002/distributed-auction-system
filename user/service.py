import user_pb2 as upb
import user_pb2_grpc as ugrpc

USERS = {"u1": "Alice", "u2": "Bob"}

class UserService(ugrpc.UserServiceServicer):
    async def GetUser(self, req, ctx):
        name = USERS.get(req.id, "Unknown")
        return upb.GetUserResponse(id=req.id, name=name)
